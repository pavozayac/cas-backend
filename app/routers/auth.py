from codecs import decode
import hashlib
from fastapi.exceptions import HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestFormStrict
from jose.exceptions import ExpiredSignatureError
from jose.jws import sign, verify
from ..resources.models import BasicLogin, Profile
import datetime
from fastapi import APIRouter, Depends, Response, Request
from ..resources import crud
from ..resources.schemas import BasicLoginIn, RegisterIn, BasicLoginSignIn, Token
from ..database import Database
from sqlalchemy.orm.session import Session
from passlib.context import CryptContext
from jose import jwt
from ..utils import CREDENTIALS_EXCEPTION
from ..settings import SECRET_KEY
from ..resources import schemas
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError
from starlette.config import Config

password_context = CryptContext(schemes=['bcrypt'])

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

#
#   Dependencies, to be injected in specific protected routes
#

def decode_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'], issuer='casportal', audience='casportal')
        email: str = payload.get('sub')

        if email is None:
            raise CREDENTIALS_EXCEPTION('Sub not found in payload')
    except ExpiredSignatureError:
        raise CREDENTIALS_EXCEPTION('Token expired')
    except JWTError as error:
        raise CREDENTIALS_EXCEPTION(error)
    except:
        raise CREDENTIALS_EXCEPTION('Invalid JWT')
    
    profile = crud.read_profile_by_email(db, email)
    
    return profile

def LoginAuth(auth: str = Depends(oauth2_scheme), db: Session = Depends(Database)):
    profile = decode_token(auth, db)

    return profile

def ModeratorAuth(profile: Profile = Depends(LoginAuth)):
    if not profile.is_moderator and not profile.is_admin:
        raise CREDENTIALS_EXCEPTION('Insufficient permissions')

def AdminAuth(profile: Profile = Depends(LoginAuth)):
    if not profile.is_admin:
        raise CREDENTIALS_EXCEPTION('Insufficient permissions')


#
#   Utility function
#

def create_token(claims: dict):
    target = claims.copy()

    target.update({
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
        'iss': 'casportal',
        'aud': 'casportal'
    })

    token = jwt.encode(target, SECRET_KEY)

    return token

# Takes 
@router.post('/register', response_model=schemas.Profile)
async def register(login: RegisterIn, db: Session = Depends(Database)):
    profile_in = schemas.ProfileIn(first_name = login.first_name, last_name = login.last_name, post_visibility = login.post_visibility)
    created_profile = crud.create_profile(db, profile_in)

    basic_in = BasicLoginIn(email=login.email, password=login.password)
    created_login = crud.create_basic_login(db, created_profile.id, basic_in)

    return created_profile


# Login sets a cookie but also returns the token object
@router.post('/login', response_model=Token)
async def login(login: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(Database)):
    basic: BasicLogin = crud.read_basic_login_by_email(db, login.username)

    if basic is None:
        raise CREDENTIALS_EXCEPTION()

    if password_context.verify(login.password, basic.password):        
        return {
            'access_token': create_token({
                'sub': basic.email
            }),
            'token_type': 'bearer'
        }
    else:
        raise CREDENTIALS_EXCEPTION()


#
#   Google authorization 
#

from google.oauth2 import id_token
from google.auth.transport import requests
from os import getenv
from jose import utils as jose_utils
import hmac

@router.post('/auth/google', response_model=Token)
async def auth_with_google(request: Request, db: Session = Depends(Database)):
    json = await request.json()
    token = json['credential']
    

    
    try:
        data: dict = id_token.verify_oauth2_token(token, requests.Request(), getenv('GOOGLE_CLIENT_ID'))
    except ValueError:
        raise HTTPException(401, 'Invalid token')

    try:
        crud.read_foreign_login(db, data['sub'])
    except HTTPException:
        profile_in = schemas.ProfileIn(first_name=data['given_name'], last_name=data.get('last_name', ''), post_visibility=0)

        profile = crud.create_profile(db, profile_in)
        crud.create_foreign_login(db, email=data['email'], profile_id=profile.id, foreign_id=data['sub'], provider='google')

    return {
        'access_token': create_token({
            'sub': data['sub']
        }),
        'token_type': 'bearer'
    }

    
    #try:
    #    profile = crud.read_profile_by_foreign_email(db, user.email)
    #except HTTPException:
    #    crud.create_foreign_login(db, user.email)


@router.post('/auth/facebook', response_model=Token)
async def auth_with_facebook(request: Request, db: Session = Depends(Database)):
    json = await request.json()
    print(json) 

    token: str = json['signed_request']

    signature, payload = token.split('.')
    
    decoded_signature = jose_utils.base64url_decode(signature + '=' * (4 - len(signature) % 4))
    calculated_signature = hmac.HMAC(bytes(getenv('FACEBOOK_CLIENT_SECRET'), 'utf-8'), bytes(payload, 'utf-8'), hashlib.sha256).digest()
  
    verified = calculated_signature == decoded_signature

    if not verified:
        raise HTTPException(401, 'Invalid signature')

    try:
        crud.read_foreign_login(db, json['id'])
    except HTTPException:
        profile_in = schemas.ProfileIn(first_name=json['first_name'], last_name=json.get('last_name', ''), post_visibility=0)

        profile = crud.create_profile(db, profile_in)
        crud.create_foreign_login(db, email=json['email'], profile_id=profile.id, foreign_id=json['id'], provider='facebook')

    return {
        'access_token': create_token({
            'sub': json['id']
        }),
        'token_type': 'bearer'
    }