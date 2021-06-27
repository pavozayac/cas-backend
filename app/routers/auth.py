from fastapi.exceptions import HTTPException
from app.models import BasicLogin
import datetime
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy import log
from .. import crud
from ..schemas import BasicLoginCreate, BasicLoginSignIn, Token
from ..dependencies import get_database
from sqlalchemy.orm.session import Session
from passlib.context import CryptContext
from jose import jwt
from ..utils import CREDENTIALS_EXCEPTION
from ..settings import SECRET_KEY

password_context = CryptContext(schemes=['bcrypt'])

router = APIRouter()


def create_token(claims: dict):
    target = claims.copy()

    target.update({'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)})

    token = jwt.encode(target, SECRET_KEY)

    return token

# Takes 
@router.post('/register')
async def register(login: BasicLoginCreate, db: Session = Depends(get_database)):
    crud.create_basic_login(db, login)

# Login sets a cookie but also returns the token object
@router.post('/login', response_model=Token)
async def login(response: Response, login: BasicLoginSignIn, db: Session = Depends(get_database)):
    basic: BasicLogin = crud.read_basic_login_by_email(db, login.email)

    if basic is None:
        raise CREDENTIALS_EXCEPTION()

    if password_context.verify(login.password, basic.password):
        response.set_cookie('auth', create_token({'sub': basic.email}), httponly=True)
        
        return {
            'token': create_token({'sub': basic.email}),
            'token_type': 'bearer'
        }
    else:
        raise CREDENTIALS_EXCEPTION()