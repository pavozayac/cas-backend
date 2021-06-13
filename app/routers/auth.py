from fastapi.exceptions import HTTPException
from app.models import BasicLogin
import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy import log
from .. import crud
from ..schemas import BasicLoginCreate, BasicLoginSignIn, Token
from ..dependencies import get_database
from sqlalchemy.orm.session import Session
from passlib.context import CryptContext
from jose import jwt
from ..utils import SECRET_KEY, CREDENTIALS_EXCEPTION

password_context = CryptContext(schemes=['bcrypt'])

router = APIRouter()


def create_token(claims: dict):
    target = claims.copy()

    target.update({'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)})

    token = jwt.encode(target, SECRET_KEY)

    return token


@router.post('/register')
async def register(login: BasicLoginCreate, db: Session = Depends(get_database)):
    crud.create_basic_login(db, login)

@router.post('/login', response_model=Token)
async def login(login: BasicLoginSignIn, db: Session = Depends(get_database)):
    basic: BasicLogin = crud.get_basic_login_by_email(db, login.email)

    if password_context.verify(login.password, basic.password):
        return {
            'token': create_token({'sub': basic.email}),
            'token_type': 'bearer'
        }
    else:
        raise CREDENTIALS_EXCEPTION