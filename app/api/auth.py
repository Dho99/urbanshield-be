from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, Role
from app.schemas.auth import UserCreate, UserOut, Token, LoginRequest
from app.core.security import hash_password, verify_password, create_token, get_current_user_optional

router = APIRouter()

ROLE_MAP = {"admin": "admin", "analyst": "analyst", "viewer": "viewer", "city_planner": "analyst", "disaster_response": "analyst", "researcher": "analyst", "policy_analyst": "viewer"}

def ensure_roles(db: Session):
    for name in ["admin", "analyst", "viewer"]:
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name))
    db.commit()

@router.post("/register", response_model=UserOut, summary="Register user")
def register(body: UserCreate, db: Session = Depends(get_db)):
    ensure_roles(db)
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    role_name = ROLE_MAP.get(body.role, "viewer")
    role = db.query(Role).filter(Role.name == role_name).first()
    u = User(email=body.email, hashed_password=hash_password(body.password), full_name=body.full_name, role_id=role.id)
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut(id=u.id, email=u.email, full_name=u.full_name, role=role.name, is_active=u.is_active)

@router.post("/login", response_model=Token, summary="Login and get JWT")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == body.email).first()
    if not u or not verify_password(body.password, u.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role = db.query(Role).filter(Role.id == u.role_id).first()
    token = create_token(u.email, role.name if role else "viewer")
    return Token(access_token=token)

@router.get("/me", response_model=UserOut, summary="Current user")
def me(user: User | None = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=role.name if role else "viewer", is_active=user.is_active)
