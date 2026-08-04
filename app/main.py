"""
# running command
uvicorn main:app --reload
"""

from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi import UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
import os
from pathlib import Path
import uvicorn
import random
from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime, timedelta
from uuid import uuid4

def _load_env_file():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            v = v.strip()
            if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
                v = v[1:-1]
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        return

_load_env_file()

from app.database import engine, Base, SessionLocal
from app import crud, models, schemas
from sqlalchemy import inspect, text
from app.ark_ocr import extract_item_from_image, ark_chat
from app.security import generate_token, hash_token
from app.defaults import default_config_json, default_extended_config_json
from app.deps import get_current_member, require_owner, get_db as deps_get_db

def ensure_items_table_columns():
    inspector = inspect(engine)
    if "items" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("items")}
    wanted = {
        "code": "TEXT",
        "type_l1": "TEXT",
        "type_l2": "TEXT",
        "household_id": "TEXT",
        "category": "TEXT",
        "location": "TEXT",
        "room": "TEXT",
        "spot": "TEXT",
        "location_free": "TEXT",
        "unit": "TEXT",
        "brand": "TEXT",
        "usage": "TEXT",
        "image_path": "TEXT",
        "min_quantity": "INTEGER",
        "purchase_date": "DATE",
        "production_date": "DATE",
        "recorded_at": "DATETIME",
        "expiry_date": "DATE",
        "barcode": "TEXT",
        "tags": "TEXT",
        "notes": "TEXT",
        "usage_status": "TEXT",
        "ownership": "TEXT",
        "price": "REAL",
        "value_score": "REAL",
        "replacement_cycle_days": "INTEGER",
        "usage_frequency": "TEXT",
        "related_item_ids": "TEXT",
        "responsible_person": "TEXT",
        "custom_json": "TEXT",
    }
    missing = [(name, sql_type) for name, sql_type in wanted.items() if name not in existing]
    if not missing:
        return
    with engine.begin() as conn:
        for name, sql_type in missing:
            conn.execute(text(f"ALTER TABLE items ADD COLUMN {name} {sql_type}"))
        if "household_id" in {n for n, _ in missing}:
            conn.execute(text("UPDATE items SET household_id = 'default' WHERE household_id IS NULL"))
        if "recorded_at" in {n for n, _ in missing}:
            conn.execute(text("UPDATE items SET recorded_at = :t WHERE recorded_at IS NULL"), {"t": datetime.utcnow().isoformat()})


def ensure_default_household():
    inspector = inspect(engine)
    if "households" not in inspector.get_table_names():
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT OR IGNORE INTO households(id, name, created_at) VALUES(:id, :name, :created_at)"
            ),
            {"id": "default", "name": "默认家庭", "created_at": datetime.utcnow().isoformat()},
        )
        if "household_config" in inspector.get_table_names():
            cfg = default_extended_config_json()
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO household_config("
                    "household_id, categories_json, locations_json, units_json, "
                    "type_tree_json, rooms_json, spots_json, responsible_people_json, area_map_json, "
                    "updated_at, updated_by_member_id"
                    ") VALUES("
                    ":hid, :c, :l, :u, :tt, :rooms, :spots, :rp, :am, :t, NULL"
                    ")"
                ),
                {
                    "hid": "default",
                    "c": cfg["categories_json"],
                    "l": cfg["locations_json"],
                    "u": cfg["units_json"],
                    "tt": cfg["type_tree_json"],
                    "rooms": cfg["rooms_json"],
                    "spots": cfg["spots_json"],
                    "rp": cfg["responsible_people_json"],
                    "am": cfg["area_map_json"],
                    "t": datetime.utcnow().isoformat(),
                },
            )


def ensure_household_config_columns():
    inspector = inspect(engine)
    if "household_config" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("household_config")}
    wanted = {
        "household_id": "TEXT",
        "categories_json": "TEXT",
        "locations_json": "TEXT",
        "units_json": "TEXT",
        "type_tree_json": "TEXT",
        "rooms_json": "TEXT",
        "spots_json": "TEXT",
        "responsible_people_json": "TEXT",
        "area_map_json": "TEXT",
        "updated_at": "DATETIME",
        "updated_by_member_id": "INTEGER",
    }
    missing = [(name, sql_type) for name, sql_type in wanted.items() if name not in existing]
    if not missing:
        return
    defaults = default_extended_config_json()
    with engine.begin() as conn:
        for name, sql_type in missing:
            conn.execute(text(f"ALTER TABLE household_config ADD COLUMN {name} {sql_type}"))
        if "type_tree_json" in {n for n, _ in missing}:
            conn.execute(text("UPDATE household_config SET type_tree_json = :v WHERE type_tree_json IS NULL"), {"v": defaults["type_tree_json"]})
        if "rooms_json" in {n for n, _ in missing}:
            conn.execute(text("UPDATE household_config SET rooms_json = :v WHERE rooms_json IS NULL"), {"v": defaults["rooms_json"]})
        if "spots_json" in {n for n, _ in missing}:
            conn.execute(text("UPDATE household_config SET spots_json = :v WHERE spots_json IS NULL"), {"v": defaults["spots_json"]})
        if "responsible_people_json" in {n for n, _ in missing}:
            conn.execute(text("UPDATE household_config SET responsible_people_json = :v WHERE responsible_people_json IS NULL"), {"v": defaults["responsible_people_json"]})
        if "area_map_json" in {n for n, _ in missing}:
            conn.execute(text("UPDATE household_config SET area_map_json = :v WHERE area_map_json IS NULL"), {"v": defaults["area_map_json"]})


def ensure_location_table():
    """Ensure location table exists and migrate old data."""
    import json
    from app.database import engine as db_engine
    from app.defaults import default_extended_config_json

    inspector = inspect(db_engine)
    # 1. Create location table if not exists
    if "location" not in inspector.get_table_names():
        models.Base.metadata.tables["location"].create(bind=db_engine)

    # 2. Add location_id column to items table if missing
    if "items" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("items")}
        if "location_id" not in existing_cols:
            with db_engine.begin() as conn:
                conn.execute(text("ALTER TABLE items ADD COLUMN location_id TEXT REFERENCES location(id) ON DELETE SET NULL"))

    # 3. Migrate HouseholdConfig rooms_json / area_map_json → Location records
    with SessionLocal() as db:
        # Skip if location table already has records
        existing_count = db.query(models.Location).count()
        if existing_count > 0:
            return

        config = db.query(models.HouseholdConfig).filter_by(household_id="default").first()
        if not config:
            return

        defaults = default_extended_config_json()
        rooms_raw = config.rooms_json or defaults.get("rooms_json", "[]")
        area_raw = config.area_map_json or defaults.get("area_map_json", "[]")

        try:
            rooms: list = json.loads(rooms_raw) if isinstance(rooms_raw, str) else rooms_raw
        except (json.JSONDecodeError, TypeError):
            rooms = []
        try:
            areas: list = json.loads(area_raw) if isinstance(area_raw, str) else area_raw
        except (json.JSONDecodeError, TypeError):
            areas = []

        # Build zone-level locations from rooms list
        zone_locations: list[models.Location] = []
        for room_name in rooms:
            loc_id = str(uuid4())
            loc = models.Location(
                id=loc_id,
                name=str(room_name),
                parent_id=None,
                level="zone",
                zone_id=loc_id,
                path=f"/{loc_id}/",
                household_id="default",
            )
            db.add(loc)
            zone_locations.append(loc)
        db.flush()

        # Build wall-level and unit-level from area_map_json
        zone_name_to_id = {loc.name: loc.id for loc in zone_locations}
        for area in areas:
            zone_name = area.get("name", "")
            zone_id = zone_name_to_id.get(zone_name)
            if not zone_id:
                continue
            walls = area.get("walls", {})
            for wall_name, wall_data in walls.items():
                wall_id = str(uuid4())
                wall_loc = models.Location(
                    id=wall_id,
                    name=str(wall_name),
                    parent_id=zone_id,
                    level="wall",
                    zone_id=zone_id,
                    path=f"/{zone_id}/{wall_id}/",
                    household_id="default",
                )
                db.add(wall_loc)
                db.flush()

                spots = wall_data.get("spots", []) if isinstance(wall_data, dict) else []
                for spot in spots:
                    spot_name = spot.get("name", str(spot)) if isinstance(spot, dict) else str(spot)
                    spot_id = str(uuid4())
                    spot_loc = models.Location(
                        id=spot_id,
                        name=spot_name,
                        parent_id=wall_id,
                        level="unit",
                        zone_id=zone_id,
                        path=f"/{zone_id}/{wall_id}/{spot_id}/",
                        household_id="default",
                    )
                    db.add(spot_loc)

        db.commit()

        # 4. Match existing item.room → Location.name to fill location_id
        q = text(
            "UPDATE items SET location_id = ("
            "  SELECT l.id FROM location l "
            "  WHERE l.household_id = items.household_id AND l.name = items.room AND l.level = 'zone'"
            "  LIMIT 1"
            ") WHERE location_id IS NULL AND room IS NOT NULL AND room != ''"
        )
        db.execute(q)
        db.commit()


# Initialize database tables
Base.metadata.create_all(bind=engine)
ensure_items_table_columns()
ensure_household_config_columns()
ensure_location_table()
ensure_default_household()

app = FastAPI(title="Warehouse API")

def _parse_csv_env(name: str) -> List[str]:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]

cors_origins = _parse_csv_env("CORS_ALLOW_ORIGINS")
if not cors_origins:
    cors_origins = [
        "http://127.0.0.1:3030",
        "http://localhost:3030",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

uploads_dir = Path(__file__).resolve().parent.parent / "data" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

get_db = deps_get_db

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
        except WebSocketDisconnect as e:
            print(f"WebSocket disconnected: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


@app.get("/api/random_numbers")
async def get_random_numbers(count: int = 10):
    numbers = [random.randint(1, 100) for _ in range(count)]
    return {"numbers": numbers}


@app.get("/api/warehouse")
async def read_warehouse():
    return {"message": "仓库主页"}


@app.get("/api")
async def read_root():
    return {"message": "主页"}


@app.get("/api/warehouse/user")
async def read_warehouse_user():
    return {"message": "仓库用户管理页"}


@app.get("/api/warehouse/manage")
async def read_warehouse_manage():
    return {"message": "录入物品信息页"}

# ================= CRUD API Endpoints =================

@app.post("/api/items", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    return crud.create_item(db=db, household_id=household.id, item=item)

@app.get("/api/items", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    items = crud.get_items(db, household_id=household.id, skip=skip, limit=limit)
    return items

@app.get("/api/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    db_item = crud.get_item_by_id(db, household_id=household.id, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/api/items/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    db_item = crud.update_item(db, household_id=household.id, item_id=item_id, item=item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete("/api/items/{item_id}", response_model=schemas.Item)
def delete_item(item_id: int, db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    db_item = crud.delete_item(db, household_id=household.id, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.post("/api/stock/outbound", response_model=schemas.OutboundResponse)
def stock_outbound(payload: schemas.OutboundRequest, db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    try:
        items, movements, low_stock_ids = crud.apply_outbound(
            db=db,
            household_id=household.id,
            member_id=member.id,
            lines=payload.lines,
        )
        return {"updated_items": items, "movements": movements, "low_stock_item_ids": low_stock_ids}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/stock/movements", response_model=List[schemas.StockMovement])
def list_stock_movements(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    return (
        db.query(models.StockMovement)
        .filter(models.StockMovement.household_id == household.id)
        .order_by(models.StockMovement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@app.post("/api/items/upload_image", response_model=dict)
async def upload_item_image(file: UploadFile = File(...), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    allowed = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported image type")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large")
    target_dir = uploads_dir / household.id
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}{suffix}"
    (target_dir / name).write_bytes(data)
    return {"image_url": f"/uploads/{household.id}/{name}"}


@app.post("/api/init/household", response_model=schemas.InitHouseholdResponse)
def init_household(payload: schemas.InitHouseholdRequest, db: Session = Depends(get_db)):
    hid = str(uuid4())
    household = models.Household(id=hid, name=payload.name)
    db.add(household)
    owner_token = generate_token()
    member = models.HouseholdMember(household_id=hid, role="owner", token_hash=hash_token(owner_token))
    db.add(member)
    defaults = default_extended_config_json()
    cfg = models.HouseholdConfig(
        household_id=hid,
        categories_json=defaults["categories_json"],
        locations_json=defaults["locations_json"],
        units_json=defaults["units_json"],
        type_tree_json=defaults["type_tree_json"],
        rooms_json=defaults["rooms_json"],
        spots_json=defaults["spots_json"],
        responsible_people_json=defaults["responsible_people_json"],
        area_map_json=defaults["area_map_json"],
        updated_at=datetime.utcnow(),
        updated_by_member_id=None,
    )
    db.add(cfg)
    db.commit()
    return schemas.InitHouseholdResponse(household_id=hid, owner_token=owner_token)


@app.get("/api/init/status", response_model=schemas.InitStatusResponse)
def init_status(db: Session = Depends(get_db)):
    default_household = db.query(models.Household).filter(models.Household.id == "default").first()
    default_items_count = db.query(models.Item).filter(models.Item.household_id == "default").count() if default_household else 0
    has_any_member = db.query(models.HouseholdMember).count() > 0
    can_adopt_default = bool(default_household) and (default_items_count > 0) and (not has_any_member)
    return schemas.InitStatusResponse(
        default_household_exists=bool(default_household),
        default_items_count=default_items_count,
        has_any_member=has_any_member,
        can_adopt_default=can_adopt_default,
    )


@app.get("/api/init/households", response_model=list[schemas.HouseholdPublicResponse])
def list_households_public(db: Session = Depends(get_db)):
    rows = db.query(models.Household).order_by(models.Household.created_at.desc()).all()
    return [
        schemas.HouseholdPublicResponse(
            household_id=h.id,
            household_name=h.name,
            created_at=h.created_at.isoformat() if h.created_at else "",
        )
        for h in rows
    ]


@app.post("/api/init/adopt_default", response_model=schemas.InitHouseholdResponse)
def adopt_default_household(db: Session = Depends(get_db)):
    has_any_member = db.query(models.HouseholdMember).count() > 0
    if has_any_member:
        raise HTTPException(status_code=403, detail="Adopt default is disabled after setup")
    household = db.query(models.Household).filter(models.Household.id == "default").first()
    if not household:
        raise HTTPException(status_code=404, detail="Default household not found")
    default_items_count = db.query(models.Item).filter(models.Item.household_id == "default").count()
    if default_items_count <= 0:
        raise HTTPException(status_code=400, detail="No items in default household")
    owner_token = generate_token()
    member = models.HouseholdMember(household_id="default", role="owner", token_hash=hash_token(owner_token))
    db.add(member)
    db.commit()
    return schemas.InitHouseholdResponse(household_id="default", owner_token=owner_token)


@app.post("/api/init/join", response_model=schemas.JoinHouseholdResponse)
def join_household(payload: schemas.JoinHouseholdRequest, db: Session = Depends(get_db)):
    household = db.query(models.Household).filter(models.Household.id == payload.household_id).first()
    if not household:
        raise HTTPException(status_code=404, detail="Household not found")
    code_hash = hash_token(payload.invite_code)
    invite = (
        db.query(models.HouseholdInvite)
        .filter(models.HouseholdInvite.household_id == payload.household_id, models.HouseholdInvite.code_hash == code_hash)
        .first()
    )
    if not invite or invite.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Invalid invite")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite expired")
    if invite.used_count >= invite.max_uses:
        raise HTTPException(status_code=400, detail="Invite exhausted")
    invite.used_count += 1
    token = generate_token()
    member = models.HouseholdMember(household_id=payload.household_id, role="user", token_hash=hash_token(token))
    db.add(member)
    db.commit()
    return schemas.JoinHouseholdResponse(household_id=payload.household_id, token=token, role="user")


@app.get("/api/me", response_model=schemas.MeResponse)
def me(member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    return schemas.MeResponse(
        household_id=household.id,
        household_name=household.name,
        member_id=member.id,
        role=member.role,
    )


@app.get("/api/config", response_model=schemas.HouseholdConfigResponse)
def get_config(db: Session = Depends(get_db), member_household: Tuple[models.HouseholdMember, models.Household] = Depends(get_current_member)):
    member, household = member_household
    cfg = db.query(models.HouseholdConfig).filter(models.HouseholdConfig.household_id == household.id).first()
    if not cfg:
        defaults = default_extended_config_json()
        cfg = models.HouseholdConfig(
            household_id=household.id,
            categories_json=defaults["categories_json"],
            locations_json=defaults["locations_json"],
            units_json=defaults["units_json"],
            type_tree_json=defaults["type_tree_json"],
            rooms_json=defaults["rooms_json"],
            spots_json=defaults["spots_json"],
            responsible_people_json=defaults["responsible_people_json"],
            area_map_json=defaults["area_map_json"],
            updated_at=datetime.utcnow(),
        )
        db.add(cfg)
        db.commit()
    import json
    defaults = default_extended_config_json()
    return schemas.HouseholdConfigResponse(
        household_id=household.id,
        categories=json.loads(cfg.categories_json or defaults["categories_json"]),
        locations=json.loads(cfg.locations_json or defaults["locations_json"]),
        units=json.loads(cfg.units_json or defaults["units_json"]),
        type_tree=json.loads(cfg.type_tree_json or defaults["type_tree_json"]),
        rooms=json.loads(cfg.rooms_json or defaults["rooms_json"]),
        spots=json.loads(cfg.spots_json or defaults["spots_json"]),
        responsible_people=json.loads(cfg.responsible_people_json or defaults["responsible_people_json"]),
        area_map=json.loads(cfg.area_map_json or defaults["area_map_json"]),
        version=2,
    )


@app.put("/api/config", response_model=schemas.HouseholdConfigResponse)
def update_config(
    payload: schemas.HouseholdConfigUpdate,
    db: Session = Depends(get_db),
    owner_household: Tuple[models.HouseholdMember, models.Household] = Depends(require_owner),
):
    owner, household = owner_household
    import json
    cfg = db.query(models.HouseholdConfig).filter(models.HouseholdConfig.household_id == household.id).first()
    if not cfg:
        cfg = models.HouseholdConfig(household_id=household.id)
        db.add(cfg)
    cfg.categories_json = json.dumps(payload.categories, ensure_ascii=False)
    cfg.locations_json = json.dumps(payload.locations, ensure_ascii=False)
    cfg.units_json = json.dumps(payload.units, ensure_ascii=False)
    if payload.type_tree is not None:
        cfg.type_tree_json = json.dumps(payload.type_tree, ensure_ascii=False)
    if payload.rooms is not None:
        cfg.rooms_json = json.dumps(payload.rooms, ensure_ascii=False)
    if payload.spots is not None:
        cfg.spots_json = json.dumps(payload.spots, ensure_ascii=False)
    if payload.responsible_people is not None:
        cfg.responsible_people_json = json.dumps(payload.responsible_people, ensure_ascii=False)
    if payload.area_map is not None:
        cfg.area_map_json = json.dumps(payload.area_map, ensure_ascii=False)
    cfg.updated_at = datetime.utcnow()
    cfg.updated_by_member_id = owner.id
    db.commit()
    defaults = default_extended_config_json()
    return schemas.HouseholdConfigResponse(
        household_id=household.id,
        categories=payload.categories,
        locations=payload.locations,
        units=payload.units,
        type_tree=json.loads(cfg.type_tree_json or defaults["type_tree_json"]),
        rooms=json.loads(cfg.rooms_json or defaults["rooms_json"]),
        spots=json.loads(cfg.spots_json or defaults["spots_json"]),
        responsible_people=json.loads(cfg.responsible_people_json or defaults["responsible_people_json"]),
        area_map=json.loads(cfg.area_map_json or defaults["area_map_json"]),
        version=2,
    )


@app.post("/api/household/invites", response_model=schemas.InviteCreateResponse)
def create_invite(
    payload: schemas.InviteCreateRequest,
    db: Session = Depends(get_db),
    owner_household: Tuple[models.HouseholdMember, models.Household] = Depends(require_owner),
):
    owner, household = owner_household
    code = generate_token()[:12]
    max_uses = payload.max_uses if payload.max_uses is not None else 10
    inv = models.HouseholdInvite(
        household_id=household.id,
        code_hash=hash_token(code),
        role="user",
        max_uses=max_uses,
        used_count=0,
        expires_at=datetime.utcnow() + timedelta(days=7),
        created_at=datetime.utcnow(),
        created_by_member_id=owner.id,
    )
    db.add(inv)
    db.commit()
    return schemas.InviteCreateResponse(
        id=inv.id,
        invite_code=code,
        expires_at=inv.expires_at.isoformat(),
        max_uses=inv.max_uses,
        used_count=inv.used_count,
        revoked=inv.revoked_at is not None,
    )


@app.get("/api/household/invites", response_model=list[schemas.InviteResponse])
def list_invites(
    db: Session = Depends(get_db),
    owner_household: Tuple[models.HouseholdMember, models.Household] = Depends(require_owner),
):
    owner, household = owner_household
    rows = (
        db.query(models.HouseholdInvite)
        .filter(models.HouseholdInvite.household_id == household.id)
        .order_by(models.HouseholdInvite.created_at.desc())
        .all()
    )
    return [
        schemas.InviteResponse(
            id=r.id,
            expires_at=r.expires_at.isoformat(),
            max_uses=r.max_uses,
            used_count=r.used_count,
            revoked=r.revoked_at is not None,
        )
        for r in rows
    ]


@app.delete("/api/household/invites/{invite_id}", response_model=dict)
def revoke_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    owner_household: Tuple[models.HouseholdMember, models.Household] = Depends(require_owner),
):
    owner, household = owner_household
    inv = (
        db.query(models.HouseholdInvite)
        .filter(models.HouseholdInvite.household_id == household.id, models.HouseholdInvite.id == invite_id)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invite not found")
    inv.revoked_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.get("/api/household/members", response_model=list[schemas.MemberResponse])
def list_members(
    db: Session = Depends(get_db),
    owner_household: Tuple[models.HouseholdMember, models.Household] = Depends(require_owner),
):
    owner, household = owner_household
    rows = (
        db.query(models.HouseholdMember)
        .filter(models.HouseholdMember.household_id == household.id)
        .order_by(models.HouseholdMember.created_at.desc())
        .all()
    )
    return [
        schemas.MemberResponse(
            id=r.id,
            role=r.role,
            created_at=r.created_at.isoformat(),
            revoked=r.revoked_at is not None,
        )
        for r in rows
    ]


@app.post("/api/household/members/{member_id}/promote", response_model=dict)
def promote_member(
    member_id: int,
    db: Session = Depends(get_db),
    owner_household: Tuple[models.HouseholdMember, models.Household] = Depends(require_owner),
):
    owner, household = owner_household
    m = (
        db.query(models.HouseholdMember)
        .filter(models.HouseholdMember.household_id == household.id, models.HouseholdMember.id == member_id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")
    if m.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Member revoked")
    m.role = "owner"
    db.commit()
    return {"ok": True}


@app.post("/api/ocr/item_extract")
async def ocr_item_extract(file: UploadFile = File(...), prompt: str = Form(default="")):
    image_bytes = await file.read()
    try:
        extracted, raw = await extract_item_from_image(
            image_bytes=image_bytes,
            filename=file.filename or "image.jpg",
            prompt_override=prompt.strip() or None,
        )
        return {"extracted": extracted, "raw": raw}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail={"error": str(e), "provider": "ark"})
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": "OCR provider call failed", "provider": "ark", "hint": str(e)})


@app.get("/api/llm/status")
async def llm_status():
    has_key = bool(os.getenv("ARK_API_KEY"))
    base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model = os.getenv("ARK_MODEL", "doubao-seed-2-0-lite-260428")
    has_httpx = True
    try:
        import httpx  # noqa: F401
    except Exception:
        has_httpx = False
    return {
        "provider": "ark",
        "api": "responses",
        "base_url": base_url,
        "model": model,
        "has_api_key": has_key,
        "has_httpx": has_httpx,
    }


@app.post("/api/llm/test")
async def llm_test(prompt: str = Form(...), file: UploadFile = File(default=None)):
    try:
        image_bytes = None
        filename = "image.jpg"
        if file is not None:
            image_bytes = await file.read()
            if len(image_bytes) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail={"error": "Image too large", "provider": "ark"})
            filename = file.filename or filename
        content, raw_json = await ark_chat(
            prompt=prompt,
            image_bytes=image_bytes,
            filename=filename,
            temperature=0.2,
        )
        return {"content": content, "raw": raw_json}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail={"error": str(e), "provider": "ark"})
    except Exception as e:
        raise HTTPException(status_code=502, detail={"error": "LLM provider call failed", "provider": "ark", "hint": str(e)})


# ── Public Location API (no auth, used by scan-to-panel page) ──

@app.get("/api/public/locations/{loc_id}")
def get_public_location(loc_id: str, db: Session = Depends(get_db)):
    """Public: get single location info (name, path, level, updated_at)."""
    loc = db.query(models.Location).filter(models.Location.id == loc_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return {
        "id": loc.id,
        "name": loc.name,
        "level": loc.level,
        "path": loc.path,
        "zone_id": loc.zone_id,
        "updated_at": str(loc.updated_at) if loc.updated_at else None,
    }

@app.get("/api/public/locations/{loc_id}/ancestors")
def get_public_location_ancestors(loc_id: str, db: Session = Depends(get_db)):
    """Public: get all ancestor locations (for breadcrumb names)."""
    loc = db.query(models.Location).filter(models.Location.id == loc_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    if not loc.path:
        return []
    ancestor_ids = [aid for aid in loc.path.strip("/").split("/") if aid and aid != loc_id]
    if not ancestor_ids:
        return []
    ancestors = (
        db.query(models.Location)
        .filter(models.Location.id.in_(ancestor_ids))
        .all()
    )
    id_order = {aid: i for i, aid in enumerate(ancestor_ids)}
    ancestors.sort(key=lambda a: id_order.get(a.id, 0))
    return [{"id": a.id, "name": a.name} for a in ancestors]

# ── Location API ──

def _build_location_tree(locations: list, parent_id: str | None = None) -> list[dict]:
    """Build nested location tree from flat list."""
    children = []
    for loc in locations:
        if loc.parent_id == parent_id:
            d = loc.__dict__.copy()
            d.pop("_sa_instance_state", None)
            d["children"] = _build_location_tree(locations, loc.id)
            children.append(d)
    return children


@app.get("/api/locations")
def get_locations(
    zone_id: str | None = None,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Get location tree, optionally filtered by zone_id."""
    member, household = member_household
    q = db.query(models.Location).filter_by(household_id=household.id)
    if zone_id:
        q = q.filter_by(zone_id=zone_id)
    all_locs = q.order_by(models.Location.sort_order, models.Location.name).all()
    if zone_id:
        return [_build_location_tree(all_locs, parent_id=zone_id)]
    return _build_location_tree(all_locs)


@app.post("/api/locations/import-from-config")
def import_locations_from_config(
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Delete all existing locations for this household and re-import from HouseholdConfig area_map / rooms."""
    import json
    from app.defaults import default_extended_config_json

    member, household = member_household
    hid = household.id

    # Delete all existing locations for this household
    db.query(models.Location).filter_by(household_id=hid).delete()
    db.flush()

    config = db.query(models.HouseholdConfig).filter_by(household_id=hid).first()
    defaults = default_extended_config_json()

    rooms_raw = config.rooms_json if config and config.rooms_json else defaults.get("rooms_json", "[]")
    area_raw = config.area_map_json if config and config.area_map_json else defaults.get("area_map_json", "[]")

    try:
        rooms: list = json.loads(rooms_raw) if isinstance(rooms_raw, str) else rooms_raw
    except (json.JSONDecodeError, TypeError):
        rooms = []
    try:
        areas: list = json.loads(area_raw) if isinstance(area_raw, str) else area_raw
    except (json.JSONDecodeError, TypeError):
        areas = []

    count = 0

    # Build zone-level locations from rooms list
    zone_name_to_id: dict[str, str] = {}
    for room_name in rooms:
        name = str(room_name).strip() if room_name else ""
        if not name:
            continue
        loc_id = str(uuid4())
        db.add(models.Location(
            id=loc_id, name=name, parent_id=None, level="zone",
            zone_id=loc_id, path=f"/{loc_id}/", household_id=hid,
        ))
        zone_name_to_id[name] = loc_id
        count += 1
    db.flush()

    # Build wall-level and unit-level from area_map_json
    for area in areas:
        zone_name = str(area.get("name", "")).strip() if isinstance(area, dict) else ""
        zone_id = zone_name_to_id.get(zone_name)
        if not zone_id:
            continue
        walls = area.get("walls", {}) if isinstance(area, dict) else {}
        for wall_name, wall_data in walls.items():
            wall_id = str(uuid4())
            db.add(models.Location(
                id=wall_id, name=str(wall_name), parent_id=zone_id, level="wall",
                zone_id=zone_id, path=f"/{zone_id}/{wall_id}/", household_id=hid,
            ))
            db.flush()
            count += 1

            spots = wall_data.get("spots", []) if isinstance(wall_data, dict) else []
            for spot in spots:
                spot_name = spot.get("name", str(spot)) if isinstance(spot, dict) else str(spot)
                spot_id = str(uuid4())
                db.add(models.Location(
                    id=spot_id, name=str(spot_name), parent_id=wall_id, level="unit",
                    zone_id=zone_id, path=f"/{zone_id}/{wall_id}/{spot_id}/", household_id=hid,
                ))
                count += 1

    db.commit()

    # Re-fetch full tree to return
    all_locs = db.query(models.Location).filter_by(household_id=hid).order_by(
        models.Location.sort_order, models.Location.name
    ).all()
    return {"imported": count, "tree": _build_location_tree(all_locs)}


@app.post("/api/locations/sync-from-area-map")
def sync_locations_from_area_map(
    body: dict,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Sync locations from area_map JSON without touching other config.
    Deletes all existing locations for this household and recreates from the area_map.
    Also writes coordinates for unit-level dots."""
    import json
    from uuid import uuid4

    member, household = member_household
    hid = household.id

    areas = body.get("area_map", [])
    if not isinstance(areas, list):
        raise HTTPException(status_code=400, detail="area_map must be a list")

    # Delete all existing locations for this household
    db.query(models.Location).filter_by(household_id=hid).delete()
    db.flush()

    count = 0

    for area in areas:
        if not isinstance(area, dict):
            continue
        zone_name = str(area.get("name", "")).strip()
        if not zone_name:
            continue
        zone_id = str(uuid4())
        db.add(models.Location(
            id=zone_id, name=zone_name, parent_id=None, level="zone",
            zone_id=zone_id, path=f"/{zone_id}/", household_id=hid,
        ))
        db.flush()
        count += 1

        walls = area.get("walls", {}) if isinstance(area, dict) else {}
        for wall_name, wall_data in walls.items():
            if not isinstance(wall_data, dict):
                continue
            wall_id = str(uuid4())
            wall_image = str(wall_data.get("image", "") or "")
            db.add(models.Location(
                id=wall_id, name=str(wall_name), parent_id=zone_id, level="wall",
                zone_id=zone_id, path=f"/{zone_id}/{wall_id}/", household_id=hid,
                map_image_url=wall_image or None,
            ))
            db.flush()
            count += 1

            # Handle dots (preferred) with fallback to legacy spots
            dots = wall_data.get("dots") if isinstance(wall_data, dict) else None
            if dots is None:
                dots = wall_data.get("spots", []) if isinstance(wall_data, dict) else []
            if not isinstance(dots, list):
                dots = []
            for dot in dots:
                if not isinstance(dot, dict):
                    continue
                dot_name = str(dot.get("name", "")).strip()
                if not dot_name:
                    dot_name = "储物单元"
                dot_id = str(uuid4())
                coords = None
                dx = dot.get("x")
                dy = dot.get("y")
                if dx is not None and dy is not None:
                    coords = json.dumps({"x": dx, "y": dy})
                db.add(models.Location(
                    id=dot_id, name=dot_name, parent_id=wall_id, level="unit",
                    zone_id=zone_id, path=f"/{zone_id}/{wall_id}/{dot_id}/", household_id=hid,
                    coordinates=coords,
                ))
                count += 1

    db.commit()

    all_locs = db.query(models.Location).filter_by(household_id=hid).order_by(
        models.Location.sort_order, models.Location.name
    ).all()
    return {"synced": count, "tree": _build_location_tree(all_locs)}


@app.post("/api/locations", response_model=schemas.LocationOut)
def create_location(
    loc: schemas.LocationCreate,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Create a location. Auto-computes level, zone_id, and path from parent_id."""
    member, household = member_household
    loc_id = str(uuid4())

    if loc.parent_id:
        parent = db.query(models.Location).filter_by(id=loc.parent_id, household_id=household.id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent location not found")
        level_map = {"zone": "wall", "wall": "unit", "unit": "sub"}
        level = level_map.get(parent.level)
        if not level:
            raise HTTPException(status_code=400, detail="Cannot create child under 'sub' level")
        zone_id = parent.zone_id
        path = f"{parent.path}{loc_id}/"
    else:
        level = "zone"
        zone_id = loc_id
        path = f"/{loc_id}/"

    new_loc = models.Location(
        id=loc_id,
        name=loc.name,
        parent_id=loc.parent_id,
        level=level,
        zone_id=zone_id,
        path=path,
        sort_order=loc.sort_order,
        map_image_url=loc.map_image_url,
        coordinates=loc.coordinates,
        household_id=household.id,
    )
    db.add(new_loc)
    db.commit()
    db.refresh(new_loc)
    return new_loc


@app.put("/api/locations/{loc_id}", response_model=schemas.LocationOut)
def update_location(
    loc_id: str,
    loc: schemas.LocationUpdate,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Update location name / coordinates / map_image_url / sort_order."""
    member, household = member_household
    target = db.query(models.Location).filter_by(id=loc_id, household_id=household.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Location not found")

    if loc.name is not None:
        target.name = loc.name
    if loc.sort_order is not None:
        target.sort_order = loc.sort_order
    if loc.map_image_url is not None:
        target.map_image_url = loc.map_image_url
    if loc.coordinates is not None:
        target.coordinates = loc.coordinates

    target.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(target)
    return target


@app.delete("/api/locations/{loc_id}")
def delete_location(
    loc_id: str,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Delete location. Cascades to children, sets item.location_id to NULL."""
    member, household = member_household
    target = db.query(models.Location).filter_by(id=loc_id, household_id=household.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Location not found")

    # Nullify location_id on associated items
    db.execute(
        text("UPDATE items SET location_id = NULL WHERE location_id = :lid"),
        {"lid": loc_id},
    )
    # Delete all descendants via path prefix match
    db.execute(
        text("DELETE FROM location WHERE household_id = :hid AND path LIKE :pat"),
        {"hid": household.id, "pat": f"{target.path}%"},
    )
    db.commit()
    return {"ok": True, "deleted_id": loc_id}


@app.post("/api/locations/{loc_id}/move", response_model=schemas.LocationOut)
def move_location(
    loc_id: str,
    move: schemas.LocationMove,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Move location under a new parent. Recomputes level, zone_id, and path for subtree."""
    member, household = member_household
    target = db.query(models.Location).filter_by(id=loc_id, household_id=household.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Location not found")

    new_parent_id = move.target_parent_id
    if new_parent_id:
        new_parent = db.query(models.Location).filter_by(id=new_parent_id, household_id=household.id).first()
        if not new_parent:
            raise HTTPException(status_code=404, detail="Target parent not found")
        # Cycle detection: target must not be ancestor of new_parent
        if new_parent.path.startswith(f"{target.path}"):
            raise HTTPException(status_code=400, detail="Cannot move a node into its own subtree")
        level_map = {"zone": "wall", "wall": "unit", "unit": "sub"}
        new_level = level_map.get(new_parent.level, "wall")
        new_zone_id = new_parent.zone_id
        new_prefix = f"{new_parent.path}{loc_id}/"
    else:
        # Move to root → become zone
        new_level = "zone"
        new_zone_id = loc_id
        new_prefix = f"/{loc_id}/"

    old_prefix = target.path
    # Update the moved node
    target.parent_id = new_parent_id
    target.level = new_level
    target.zone_id = new_zone_id
    # Update path for self and all descendants
    descendants = db.query(models.Location).filter(
        models.Location.household_id == household.id,
        models.Location.path.like(f"{old_prefix}%"),
    ).all()
    for d in descendants:
        d.path = d.path.replace(old_prefix, new_prefix, 1)
        if d.id == loc_id:
            d.path = new_prefix
    # Update zone_id for descendants
    for d in descendants:
        if d.id != loc_id:
            d.zone_id = new_zone_id

    target.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(target)
    return target


@app.post("/api/locations/batch-delete")
def batch_delete_locations(
    req: schemas.BatchDeleteRequest,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Batch delete locations that have no items associated."""
    member, household = member_household
    if not req.ids:
        raise HTTPException(status_code=400, detail="No location IDs provided")

    deleted = []
    for lid in req.ids:
        target = db.query(models.Location).filter_by(id=lid, household_id=household.id).first()
        if not target:
            continue
        # Only delete if no items reference this location or its descendants
        descendant_ids = db.execute(
            text("SELECT id FROM location WHERE household_id = :hid AND path LIKE :pat"),
            {"hid": household.id, "pat": f"{target.path}%"},
        ).fetchall()
        all_ids = [lid] + [row[0] for row in descendant_ids if row[0] != lid]
        item_count = db.query(models.Item).filter(
            models.Item.household_id == household.id,
            models.Item.location_id.in_(all_ids),
        ).count()
        if item_count > 0:
            continue
        db.execute(text("DELETE FROM location WHERE id IN ({})".format(",".join(f"'{i}'" for i in all_ids))))
        deleted.append(lid)

    db.commit()
    return {"ok": True, "deleted_ids": deleted}


@app.get("/api/locations/{loc_id}/qrcode")
def get_location_qrcode(
    loc_id: str,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Generate QR code PNG for a location."""
    import qrcode
    from io import BytesIO
    from fastapi.responses import Response

    member, household = member_household
    target = db.query(models.Location).filter_by(id=loc_id, household_id=household.id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Location not found")

    host = os.getenv("PUBLIC_HOST", "http://127.0.0.1:3030")
    content = f"{host}/location/{loc_id}?action=panel"

    img = qrcode.make(content)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")


@app.post("/api/locations/qrcodes/batch")
def batch_location_qrcodes(
    body: dict,
    db: Session = Depends(get_db),
    member_household: tuple = Depends(get_current_member),
):
    """Batch generate QR code labels as a PDF (A4, 6 per page)."""
    import qrcode
    from io import BytesIO
    from fastapi.responses import Response
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as pdf_canvas

    member, household = member_household
    ids = body.get("ids")
    if not ids or not isinstance(ids, list):
        raise HTTPException(status_code=400, detail="ids must be a non-empty list")
    if len(ids) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 ids allowed")

    locations = db.query(models.Location).filter(
        models.Location.id.in_(ids),
        models.Location.household_id == household.id,
    ).all()

    if not locations:
        raise HTTPException(status_code=400, detail="No matching locations found")

    # sort by path for consistent label ordering
    locations.sort(key=lambda l: l.path or "")

    host = os.getenv("PUBLIC_HOST", "http://127.0.0.1:3030")

    # resolve parent IDs to names for display paths
    all_parent_ids = set()
    for loc in locations:
        if loc.path:
            for pid in loc.path.strip("/").split("/"):
                all_parent_ids.add(pid)
    parent_map = {}
    if all_parent_ids:
        parent_locs = db.query(models.Location).filter(
            models.Location.id.in_(list(all_parent_ids))
        ).all()
        parent_map = {pl.id: (pl.name, pl.level) for pl in parent_locs}

    # generate QR images in memory
    qr_data = []
    qr_size = 45 * mm
    for loc in locations:
        content = f"{host}/location/{loc.id}?action=panel"
        img = qrcode.make(content)
        name = loc.name or ""
        # build display path: zone - wall - slot
        ancestors = loc.path.strip("/").split("/") if loc.path else []
        # collect (name, level) from ancestors + self
        all_parts = []
        for pid in ancestors:
            entry = parent_map.get(pid)
            if entry:
                all_parts.append(entry)
            else:
                all_parts.append((pid, ''))
        all_parts.append((name, loc.level))
        # extract by level
        zone_name = next((n for n, l in all_parts if l == 'zone'), '')
        wall_name = next((n for n, l in all_parts if l == 'wall'), '')
        slot_name = next((n for n, l in all_parts if l == 'unit'), '')
        qr_data.append((img, zone_name, wall_name, slot_name))

    # build PDF
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    pdfmetrics.registerFont(TTFont('NotoSansSC', os.path.join(font_dir, 'NotoSansSC-Regular.ttf')))
    pdfmetrics.registerFont(TTFont('NotoSansSC-Bold', os.path.join(font_dir, 'NotoSansSC-Bold.ttf')))

    pdf_buf = BytesIO()
    c = pdf_canvas.Canvas(pdf_buf, pagesize=A4)
    page_w, page_h = A4  # 595.27 x 841.89 pt
    margin_x = 15 * mm
    margin_y = 15 * mm
    cols = 3
    rows = 2
    cell_w = (page_w - 2 * margin_x) / cols
    cell_h = (page_h - 2 * margin_y) / rows

    for idx, (img, zone_name, wall_name, slot_name) in enumerate(qr_data):
        page_idx = idx % (cols * rows)
        col = page_idx % cols
        row = rows - 1 - (page_idx // cols)  # top-to-bottom

        x = margin_x + col * cell_w + cell_w / 2
        y = margin_y + row * cell_h + cell_h / 2

        # draw QR centered
        qr_x = x - qr_size / 2
        qr_y = y + 5 * mm
        c.drawImage(ImageReader(img.convert('RGB')), qr_x, qr_y, width=qr_size, height=qr_size)

        # label text below QR: 区域 / 墙面 / 收纳位
        text_x = x - qr_size / 2
        line_y = qr_y - 8 * mm
        c.setFont("NotoSansSC", 8)
        c.drawString(text_x, line_y, f"区域：    {zone_name or '-'}")
        c.drawString(text_x, line_y - 7 * mm, f"墙面：    {wall_name or '-'}")
        c.drawString(text_x, line_y - 14 * mm, f"收纳位：{slot_name or '-'}")

        # new page after 6 labels
        if (idx + 1) % (cols * rows) == 0 and idx + 1 < len(qr_data):
            c.showPage()

    c.save()
    pdf_buf.seek(0)
    return Response(
        content=pdf_buf.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=location-qrcodes.pdf"},
    )


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 18808))  # Default to 8000 if not set
    print("port is ", port)
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
