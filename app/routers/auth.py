import hmac
from jose import utils as jose_utils
from os import getenv
from google.auth.transport import requests
from google.oauth2 import id_token
from codecs import decode
import hashlib
from fastapi.exceptions import HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestFormStrict
from jose.exceptions import ExpiredSignatureError
from jose.jws import sign, verify
from starlette.responses import JSONResponse
from starlette.status import HTTP_409_CONFLICT
from ..resources.models import BasicLogin, Profile
import datetime
from fastapi import APIRouter, Depends, Response, Request, Cookie
from ..resources import crud
from ..resources.schemas import BasicLoginIn, RegisterIn, BasicLoginSignIn, Token
from ..database import Database
from sqlalchemy.orm.session import Session
from passlib.context import CryptContext
from jose import jwt
from ..utils import CREDENTIALS_EXCEPTION, generate_random_code
from ..settings import SECRET_KEY
from ..resources import schemas
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError
from starlette.config import Config
from typing import Optional
from ..mailing import send_confirmation_mail, send_recovery_mail
from app.resources import models

password_context = CryptContext(schemes=['bcrypt'])

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

#
#   Dependencies, to be injected in specific protected routes
#


def decode_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[
                             'HS256'], issuer='casportal', audience='casportal')
        sub: str = payload.get('sub')
        foreign: bool = payload.get('foreign')

        if sub is None:
            raise CREDENTIALS_EXCEPTION('Sub not found in payload')
    except ExpiredSignatureError:
        raise CREDENTIALS_EXCEPTION('Token expired')
    except JWTError as error:
        raise CREDENTIALS_EXCEPTION(error)
    except:
        raise CREDENTIALS_EXCEPTION('Invalid JWT')

    if foreign:
        return crud.read_profile_by_foreign_id(db, sub), True
    else:
        return crud.read_profile_by_email(db, sub), False


def LoginAuth(casportal_token: str = Cookie(None), db: Session = Depends(Database)):
    profile, is_foreign = decode_token(casportal_token, db)

    if not is_foreign:
        basic_login = crud.read_basic_login_by_profile(db, profile.id)

        if not basic_login.verified:
            if basic_login.verification_sent:
                raise CREDENTIALS_EXCEPTION('The verification has already been sent.')
            else:
                raise CREDENTIALS_EXCEPTION('The verification could not be sent, please try to create anonther account.')

    return profile

def AdminAuth(profile: Profile = Depends(LoginAuth)):
    if not profile.is_admin:
        raise CREDENTIALS_EXCEPTION('Insufficient permissions')

    return profile


#
#   Utility function
#

def create_token(claims: dict):
    target = claims.copy()

    target.update({
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
        'iss': 'casportal',
        'aud': 'casportal'
    })

    token = jwt.encode(target, SECRET_KEY)

    return token

# Takes


@router.post('/register', response_model=schemas.Profile)
async def register(login: RegisterIn, db: Session = Depends(Database)):
    profile_in = schemas.ProfileIn(
        first_name=login.first_name, last_name=login.last_name)
    created_profile = crud.create_profile(db, profile_in)

    basic_in = BasicLoginIn(email=login.email, password=login.password)
    created_login = crud.create_basic_login(db, created_profile.id, basic_in)

    random_code = generate_random_code()

    crud.create_confirmation_code(db, random_code, created_profile.id)

    await send_confirmation_mail(created_login.email, random_code)

    created_login.verification_sent = True

    db.commit()

    return created_profile


@router.post('/confirm-email/{code}')
async def confirm_email_route(code: str, db: Session = Depends(Database)):
    confirmation_code = crud.read_confirmation_code(db, code)

    basic_login = crud.read_basic_login_by_profile(
        db, confirmation_code.profile_id)

    basic_login.verified = True

    crud.delete_confirmation_code(db, confirmation_code)

    db.commit()

    return {
        'detail': 'Successfully confirmed email address'
    }


@router.post('/send-recovery-mail')
async def send_recovery_mail_route(recovery_mail_schema: schemas.SendRecoveryMailSchema, db: Session = Depends(Database)):
    profile = crud.read_profile_by_email(db, recovery_mail_schema.email)

    random_code_str = generate_random_code()
    code = crud.create_confirmation_code(db, random_code_str, profile.id)

    try:
        await send_recovery_mail(recovery_mail_schema.email, random_code_str)
    except:
        crud.delete_confirmation_code(db, code)
        raise HTTPException(HTTP_409_CONFLICT, 'Could not send recovery mail')

    return {
        'detail': 'Recovery mail has been sent'
    }


@router.post('/recover-password/{code}')
async def recover_password(code: str, basic_login_in: schemas.BasicLoginIn, db: Session = Depends(Database)):
    confirmation_code = crud.read_confirmation_code(db, code)

    basic_login = crud.read_basic_login_by_profile(
        db, confirmation_code.profile_id)

    crud.update_basic_login(db, basic_login, basic_login_in)

    crud.delete_confirmation_code(db, confirmation_code)

    return {
        'detail': 'Password reset successfully'
    }


@router.post('/change-password')
async def change_password(basic_login_in: schemas.BasicLoginIn, profile: models.Profile = Depends(LoginAuth), db: Session = Depends(Database)):
    basic_login = profile.basic_login

    crud.update_basic_login(db, basic_login, basic_login_in)

    return {
        'detail': 'Password change successfully'
    }


# Login sets a cookie but also returns the token object
@router.post('/login')
async def login(response: Response, login: schemas.BasicLoginSignIn, db: Session = Depends(Database)):
    basic: BasicLogin = crud.read_basic_login_by_email(db, login.email)

    if basic is None:
        raise CREDENTIALS_EXCEPTION()

    if not basic.verified:
        if basic.verification_sent:
            raise CREDENTIALS_EXCEPTION('The verification has already been sent.')
        else:
            raise CREDENTIALS_EXCEPTION('The verification could not be sent, please try to create anonther account.')

    if password_context.verify(login.password, basic.password):
        token = create_token({
            'sub': basic.email
        })

        # response = JSONResponse(content = {
        #     'access_token': token,
        #     'token_type': 'bearer'
        # })
        response.set_cookie(key='casportal_token',
                            value=token, path='/', httponly=True)

        return {
            'access_token': token,
            'token_type': 'bearer'
        }
    else:
        raise CREDENTIALS_EXCEPTION()


@router.post('/logout')
async def logout(response: Response):
    response.delete_cookie('casportal_token', path='/')

    return {
        'detail': 'Deleted cookie'
    }


#
#   Google authorization
#


@router.post('/auth/google', response_model=Token)
async def auth_with_google(response: Response, request: Request, db: Session = Depends(Database)):
    json = await request.json()
    token = json['credential']

    try:
        data: dict = id_token.verify_oauth2_token(
            token, requests.Request(), getenv('GOOGLE_CLIENT_ID'))
    except ValueError:
        raise HTTPException(401, 'Invalid token')

    try:
        crud.read_foreign_login(db, data['sub'])
    except HTTPException:
        profile_in = schemas.ProfileIn(first_name=data['given_name'], last_name=data.get(
            'last_name', ''))

        profile = crud.create_profile(db, profile_in)
        crud.create_foreign_login(
            db, email=data['email'], profile_id=profile.id, foreign_id=data['sub'], provider='google')

    access_token = create_token({
        'sub': data['sub'],
        'foreign': True
    })

    response.set_cookie(key='casportal_token',
                        value=access_token, path='/', httponly=True)

    return {
        'access_token': access_token,
        'token_type': 'bearer'
    }
