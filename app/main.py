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

# Initialize database tables
Base.metadata.create_all(bind=engine)
ensure_items_table_columns()
ensure_household_config_columns()
ensure_default_household()

app = FastAPI(title="Warehouse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
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


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 18808))  # Default to 8000 if not set
    print("port is ", port)
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
