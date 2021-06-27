from app.models import Profile
from fastapi.param_functions import Depends
from app.crud import read_profile_by_email
from typing import Optional

from jose.constants import ALGORITHMS
from .database import SessionLocal
from fastapi import Cookie
from jose import jwt, JWTError
from .utils import SECRET_KEY, CREDENTIALS_EXCEPTION
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
    
    profile = read_profile_by_email(db, email)

    if profile is None:
        raise CREDENTIALS_EXCEPTION('Associated profile not found')
    return profile

def ModeratorAuth(profile: Profile = Depends(LoginAuth)):
    if profile.is_moderator != True:
        raise CREDENTIALS_EXCEPTION(detail='Invalid permissions')

