import os
from datetime import datetime, timedelta, timezone
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from config.collection import admin_registartion_collection


load_dotenv(override=True)

# Supports both correctly spelled names and existing legacy typos.
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SCERET_KEY")
ALGORITHM = os.getenv("ALGORITHM") or os.getenv("ALOGORITH") or "HS256"
TOKEN_EXPIRE = os.getenv("TOKEN_EXPIRE")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(TOKEN_EXPIRE or 30)
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin-registration/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_access_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY (or SCERET_KEY) is not configured")

    to_encode = data.copy()
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire_at})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY (or SCERET_KEY) is not configured")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        raise _credentials_exception() from exc


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    payload = decode_access_token(token)
    email = payload.get("email")
    if not email:
        raise _credentials_exception()

    admin = await admin_registartion_collection.find_one({"email": email})
    if not admin:
        raise _credentials_exception()

    admin["id"] = str(admin.pop("_id"))
    return admin


