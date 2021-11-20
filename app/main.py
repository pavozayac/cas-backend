from .utils import CREDENTIALS_EXCEPTION
from sqlalchemy.orm.session import Session
from fastapi import FastAPI, Depends, HTTPException, status
from .resources.schemas import Message, ProfileIn
from .database import engine, Base, Database
from .routers.auth import LoginAuth
from typing import List
from os import path, makedirs
from app import settings
from fastapi.middleware.cors import CORSMiddleware

from .resources import models, crud, schemas

from .routers import auth, profiles, notifications, groups, reflections, tags, messages

api = FastAPI()

Base.metadata.create_all(bind=engine)

if not path.exists(settings.ATTACHMENT_PATH):
    makedirs(settings.ATTACHMENT_PATH)

origins = [
    'http://localhost:3000',
    'http://localhost:5000'
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(
    auth.router,
    prefix='',
    tags=['auth']
)

api.include_router(
    profiles.router,
    prefix='/profiles',
    tags=['profiles']
)

api.include_router(
    notifications.router,
    prefix='/post-notifications',
    tags=['post_notifications']
)

api.include_router(
    groups.router,
    prefix='/groups',
    tags=['groups']
)

api.include_router(
    reflections.router,
    prefix='/reflections',
    tags=['reflections']
)

api.include_router(
    tags.router,
    prefix='/tags',
    tags=['tags']
)

api.include_router(
    messages.router,
    prefix='',
    tags=['messages']
)


# @api.get('/bruh', response_model=schemas.Profile)
# async def root(profile: models.Profile = Depends(LoginAuth)):
#     if profile is None:
#         raise CREDENTIALS_EXCEPTION('Error in main')
#     return profile