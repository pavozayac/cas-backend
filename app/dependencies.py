from sqlalchemy.engine.interfaces import CreateEnginePlugin
from .resources.models import Profile
from fastapi.param_functions import Depends
from .resources import crud
from typing import Optional

from .database import SessionLocal
from fastapi import Cookie
from jose import jwt, JWTError
from .utils import CREDENTIALS_EXCEPTION
from .settings import SECRET_KEY
from sqlalchemy.orm.session import Session

def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def LoginAuth(auth: Optional[str] = Cookie(None), db: Session = Depends(get_database)):
    if auth is None:
        raise CREDENTIALS_EXCEPTION('Auth cookie not provided')
    try:
        payload = jwt.decode(auth, SECRET_KEY, algorithms=['HS256'])
        email: str = payload.get('sub')

        if email is None:
            raise CREDENTIALS_EXCEPTION('Sub not found in payload')
    except JWTError:
        raise CREDENTIALS_EXCEPTION('Decoding failed')
    
    profile = crud.read_profile_by_email(db, email)

    if profile is None:
        raise CREDENTIALS_EXCEPTION('Associated profile not found')
    return profile

def ModeratorAuth(profile: Profile = Depends(LoginAuth)):
    if not profile.is_moderator and not profile.is_admin:
        raise CREDENTIALS_EXCEPTION('Insufficient permissions')

def AdminAuth(profile: Profile = Depends(LoginAuth)):
    if not profile.is_admin:
        raise CREDENTIALS_EXCEPTION('Insufficient permissions')
