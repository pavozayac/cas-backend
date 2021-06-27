from .. import crud, schemas
from fastapi import APIRouter, Depends
from typing import List, Optional
from sqlalchemy.orm.session import Session
from ..dependencies import get_database, LoginAuth
from ..models import Profile

router = APIRouter()

@router.get('/', response_model=List[schemas.Profile])
def get_profiles(db: Session = Depends(get_database)):
    return crud.read_profiles(db)

@router.get('/current', response_model=schemas.Profile)
async def get_current_logged_in_profile(profile: Profile = Depends(LoginAuth)):
    return profile

@router.get('/id/{id}', response_model=schemas.Profile)
async def get_profile(id: int, db: Session = Depends(get_database)):
    return crud.read_profile_by_id(db, id)

@router.get('/notifications', response_model=List[schemas.Notification])
async def get_profile_notifications(profile: Profile = Depends(LoginAuth)):
    return profile.notifications