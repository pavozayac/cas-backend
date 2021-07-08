from pydantic.schema import schema
from ..resources import crud, schemas
from fastapi import APIRouter, Depends
from typing import List, Optional
from sqlalchemy.orm.session import Session
from ..dependencies import get_database, LoginAuth
from ..resources.models import Profile

router = APIRouter()

@router.get('/', response_model=List[schemas.Profile])
def get_profiles(db: Session = Depends(get_database)):
    return crud.read_profiles(db)

@router.post('/filter', response_model=List[schemas.Profile])
def search_profiles(filters: schemas.ProfileFilters, sorts: schemas.ProfileSorts, db: Session = Depends(get_database)):
    return crud.filter_profiles(db, filters, sorts)

@router.get('/current', response_model=schemas.Profile)
async def get_current_logged_in_profile(profile: Profile = Depends(LoginAuth)):
    return profile

@router.get('/id/{id}', response_model=schemas.Profile)
async def get_profile(id: int, db: Session = Depends(get_database)):
    return crud.read_profile_by_id(db, id)

@router.get('/notifications', response_model=List[schemas.Notification])
async def get_profile_notifications(profile: Profile = Depends(LoginAuth)):
    return profile.notifications