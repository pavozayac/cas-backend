from app.utils import CREDENTIALS_EXCEPTION
from sqlalchemy.orm.session import Session
from fastapi import FastAPI, Depends, HTTPException, status
from .schemas import ProfileIn
from .database import engine
from .dependencies import get_database, LoginAuth
from typing import List

from . import models, crud, schemas

from .routers import auth, profiles, post_notifications

api = FastAPI()

api.include_router(
    auth.router,
    prefix='/auth',
    tags=['auth']
)

api.include_router(
    profiles.router,
    prefix='/profiles',
    tags=['profiles']
)

api.include_router(
    post_notifications.router,
    prefix='/post-notifications',
    tags=['post_notifications']
)

models.Base.metadata.create_all(bind=engine)

@api.get('/bruh', response_model=schemas.Profile)
async def root(profile: models.Profile = Depends(LoginAuth)):
    if profile is None:
        raise CREDENTIALS_EXCEPTION('Error in main')
    return profile
