from sqlalchemy.orm.session import Session
from fastapi import FastAPI, Depends, HTTPException, status
from .schemas import ProfileIn
from .database import engine
from .dependencies import get_database, JWTAuth
from typing import List

from . import models, crud, schemas

from .routers import auth

api = FastAPI()

api.include_router(
    auth.router,
    prefix='/auth',
    tags=['auth']
)

models.Base.metadata.create_all(bind=engine)

@api.get('/bruh/{id}')
async def root(id: int, profile = Depends(JWTAuth)):
    return {'Returned id': id}

@api.get('/profiles', response_model=List[schemas.Profile])
def get_profiles(db: Session = Depends(get_database)):
    return crud.read_profiles(db)

@api.post('/profiles')
async def create_profile(profile: ProfileIn, db: Session = Depends(get_database)):
    return crud.create_profile(db, profile)