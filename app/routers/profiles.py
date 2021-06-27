from .. import crud, schemas
from fastapi import APIRouter, Depends
from typing import List, Optional
from sqlalchemy.orm.session import Session
from ..dependencies import get_database

router = APIRouter()

@router.get('/profiles', response_model=List[schemas.Profile])
def get_profiles(db: Session = Depends(get_database)):
    return crud.read_profiles(db)

@router.post('/profiles')
async def create_profile(profile: schemas.ProfileIn, db: Session = Depends(get_database)):
    return crud.create_profile(db, profile)
