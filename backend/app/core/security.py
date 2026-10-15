import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from app.database.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)

# bcrypt hard limit 72 bytes; truncate agar tak ValueError (hash lama $2b$ tetap valid).
def _pw_bytes(p: str) -> bytes:
    return p.encode("utf-8")[:72]

def hash_password(p: str) -> str:
    return bcrypt.hashpw(_pw_bytes(p), bcrypt.gensalt()).decode("utf-8")

def verify_password(p: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(_pw_bytes(p), h.encode("utf-8"))
    except Exception:
        return False

def create_token(sub: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": sub, "role": role, "exp": exp}, SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_user_optional(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    if not creds:
        return None
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        return db.query(User).filter(User.email == email).first()
    except JWTError:
        return None

def require_role(*roles: str):
    def _check(user: User | None = Depends(get_current_user_optional)):
        if not roles:
            return user
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        r = (user.role.name if hasattr(user.role, "name") else str(user.role_id)).lower()
        if r not in [x.lower() for x in roles]:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return _check
