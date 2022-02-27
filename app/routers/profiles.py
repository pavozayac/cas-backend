from os import getenv
from sys import prefix
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from pydantic.schema import schema
from pydantic.utils import deep_update
from ..resources import crud, schemas, models
from fastapi import APIRouter, Depends, Form
from typing import List, Optional
from sqlalchemy.orm.session import Session
from .auth import LoginAuth
from ..database import Database
from ..resources.models import Profile, ProfileAvatar
from fastapi.responses import FileResponse

router = APIRouter()

#
#   Advanced queries for profiles
#

@router.post('/query', response_model=schemas.BulkProfileResponse)
def search_profiles(filters: schemas.ProfileFilters, sorts: schemas.ProfileSorts, db: Session = Depends(Database), pagination: Optional[schemas.Pagination] = None, profile: models.Profile = Depends(LoginAuth)):
    profiles, count = crud.filter_profiles(db, pagination, filters, sorts)
    
    return schemas.BulkProfileResponse(items=profiles, count=count)

#
#   CRUD actions for profiles
#

@router.get('/', response_model=List[schemas.Profile])
def get_profiles(db: Session = Depends(Database)):
    return crud.read_profiles(db)


@router.get('/current', response_model=schemas.Profile)
async def get_current_logged_in_profile(profile: Profile = Depends(LoginAuth)):
    return profile

@router.get('/id/{id}', response_model=schemas.Profile)
async def get_profile(id: int, db: Session = Depends(Database)):
    return crud.read_profile_by_id(db, id)

@router.get('/notifications', response_model=List[schemas.Notification])
async def get_profile_notifications(profile: Profile = Depends(LoginAuth)):
    return profile.notifications

@router.put('/current', response_model=schemas.Profile)
async def put_current_profile(data: schemas.ProfileIn, profile: Profile = Depends(LoginAuth), db: Session = Depends(Database)):
    return crud.update_profile(db, profile, data)

@router.put('/current/leave-group', response_model=schemas.Profile)
async def leave_current_group(profile: Profile = Depends(LoginAuth), db: Session = Depends(Database)):
    if profile.group.coordinator_id == profile.id:
        group = crud.read_group_by_id(db, profile.group_id)
        crud.delete_group(db, group)
    
    profile.group = None

    db.commit()
    db.refresh(profile)
    
    return profile

@router.delete('/current')
async def delete_current_profile(profile: Profile = Depends(LoginAuth), db: Session = Depends(Database)):
    crud.delete_profile(db, profile)

    return {
        'detail': 'Successfully deleted profile'
    }

#
#   CRUD for avatar, profile avatars will be available to everyone logged in 
#

@router.get('/avatar/{id}')
async def get_avatar_by_id(id: str, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    print('bruh')
    avatar = crud.read_profile_avatar(db, id)

    return FileResponse(avatar.saved_path)

@router.post('/avatar', response_model=schemas.Avatar)
async def add_profile_avatar(file: UploadFile = Form(...), db: Session = Depends(Database), profile: Profile = Depends(LoginAuth)):
    avatar_in = schemas.AvatarIn(filename=file.filename)
    avatar = await crud.create_profile_avatar(db, avatar_in, profile, file)

    return avatar

@router.put('/avatar', response_model=schemas.Avatar)
async def update_profile_avatar(file: UploadFile = Form(...), db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    avatar_in = schemas.AvatarIn(filename=file.filename)
    avatar = await crud.update_profile_avatar(db, avatar_in, profile, file)

    return avatar

@router.delete('/avatar')
async def delete_profile_avatar(db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    crud.delete_profile_avatar(db, profile)

    return {
        'detail': 'Successfully deleted profile avatar'
    }