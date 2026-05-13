from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Tuple

from app.database import SessionLocal
from app.models import HouseholdMember, Household
from app.security import hash_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _parse_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2:
        return None
    if parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token if token else None


def get_current_member(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
) -> Tuple[HouseholdMember, Household]:
    token = _parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization")
    token_hash = hash_token(token)
    member = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.token_hash == token_hash)
        .first()
    )
    if not member or member.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid token")
    household = db.query(Household).filter(Household.id == member.household_id).first()
    if not household:
        raise HTTPException(status_code=401, detail="Invalid household")
    return member, household


def require_owner(member_household: Tuple[HouseholdMember, Household] = Depends(get_current_member)) -> Tuple[HouseholdMember, Household]:
    member, household = member_household
    if member.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")
    return member, household

