from ..models import BasicLogin
import datetime
from fastapi import APIRouter, Depends, Response
from .. import crud
from ..schemas import BasicLoginIn, RegisterIn, BasicLoginSignIn, Token
from ..dependencies import get_database
from sqlalchemy.orm.session import Session
from passlib.context import CryptContext
from jose import jwt
from ..utils import CREDENTIALS_EXCEPTION
from ..settings import SECRET_KEY
from app import schemas

password_context = CryptContext(schemes=['bcrypt'])

router = APIRouter()


def create_token(claims: dict):
    target = claims.copy()

    target.update({'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)})

    token = jwt.encode(target, SECRET_KEY)

    return token

# Takes 
@router.post('/register', response_model=schemas.BasicLogin)
async def register(login: RegisterIn, db: Session = Depends(get_database)):
    profile_in = schemas.ProfileIn(first_name = login.first_name, last_name = login.last_name, post_visibility = login.post_visibility)
    created_profile = crud.create_profile(db, profile_in)

    basic_in = BasicLoginIn(email=login.email, password=login.password)
    created_login = crud.create_basic_login(db, created_profile.id, basic_in)

    return created_login


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