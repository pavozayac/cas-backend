from fastapi import APIRouter, UploadFile, Form
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse
from pydantic.schema import schema
from sqlalchemy.orm.session import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from ..resources import crud, schemas, models
from .auth import LoginAuth
from ..database import Database
from ..utils import check_object_ownership, sort_from_schema, filter_from_schema
from typing import List, Optional
from sqlalchemy.orm.exc import NoResultFound

router = APIRouter()

#
#   Advanced queries for groups
#

@router.post('/query', response_model=List[schemas.BulkGroup])
async def filter_groups(filters: schemas.GroupFilters, sorts: schemas.GroupSorts, db: Session = Depends(Database)):
    return crud.filter_groups(db, filters, sorts)

#
#   CRUD for groups
#

@router.post('/', response_model=schemas.Group)
async def add_group(group: schemas.GroupIn, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    if profile.group is not None:
        raise HTTPException(HTTP_409_CONFLICT, 'You are already a coordinator of another group.')

    return crud.create_group(db, group, profile.id)

@router.get('/{id}', response_model=schemas.Group)
async def get_group(id: str, db: Session = Depends(Database)):
    try:
        group = crud.read_group_by_id(db, id)
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Group not found')
    
    return crud.read_group_by_id(db, id)

@router.put('/{id}', response_model=schemas.Group)
async def put_group(id: str, data: schemas.GroupIn, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    try:
        group = crud.read_group_by_id(db, id)
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Group not found')

    check_object_ownership(group, profile, 'coordinator_id')

    return crud.update_group(db, group, data)


@router.delete('/{id}')
async def delete_group(id: str, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    try:
        group = crud.read_group_by_id(db, id)
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Group not found')
    
    
    check_object_ownership(group, profile, 'coordinator_id')
    
    crud.delete_group(db, group)

    return {
        'detail': 'Successfully deleted the group'
    }

#
#   CRUD and additional actions for join requests
#

@router.get('/{id}/join-requests', response_model=List[schemas.GroupJoinRequest])
async def get_join_requests(id: str, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    group = crud.read_group_by_id(db, id)
    check_object_ownership(group, profile, 'coordinator_id')

    return group.group_requests

@router.post('/{id}/accept-request/{profile_id}')
async def accept_group_join_request(id: str, profile_id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    group = crud.read_group_by_id(db, id)
    check_object_ownership(group, profile, 'coordinator_id')

    request = crud.read_group_join_request_by_ids(db, id, profile_id)

    request.profile.group = request.group
    
    notification = models.Notification(
        profile_id = request.profile_id,
        content = f'Your request to join {request.group.name} has been denied.'
    )

    notification.recipients = [request.profile]

    db.add(notification)
    db.delete(request)
    db.commit()

    return {
        'detail': 'The request has been deleted and a notification has been sent to the user'
    }
    

@router.post('/{id}/deny-request/{profile_id}')
async def accept_group_join_request(group_id: str, profile_id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    group = crud.read_group_by_id(db, id)
    check_object_ownership(group, profile, 'coordinator_id')
    
    request = crud.read_group_join_request_by_ids(db, group_id, profile_id)

    notification = models.Notification(
        profile_id = request.profile_id,
        content = f'Your request to join {request.group.name} has been denied.'
    )

    notification.recipients = [request.profile]

    db.add(notification)
    db.delete(request)
    db.commit()

    return {
        'detail': 'The request has been deleted and a notification has been sent to the user'
    }


@router.post('/{id}/join-requests', response_model=schemas.GroupJoinRequest)
async def post_join_request(id: str, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    if profile.group is not None:
        raise HTTPException(HTTP_409_CONFLICT, 'In order to send a join request you need to leave the current group.')

    group = crud.read_group_by_id(db, id)

    if group is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Not group with such id exists.')

    return crud.create_group_join_request(db, profile.id, id)

@router.delete('/{id}/delete-member/{profile_id}')
async def delete_group_member(id: str, profile_id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    group = crud.read_group_by_id(db, id)
    check_object_ownership(group, profile, 'coordinator_id')

    profile = crud.read_profile_by_id(db, profile_id)

    if profile is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Profile with this id does not exist.')

    profile.group_id = None

    db.commit()

#
#   CRUD for avatar
#

@router.get('/avatar/{id}/')
async def get_avatar_by_id(id: str, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    avatar = crud.read_group_avatar(db, id)
    print(avatar.saved_path)

    return FileResponse(avatar.saved_path)

# @router.post('/avatar', response_model=schemas.Avatar)
# async def add_group_avatar(file: UploadFile = Form(...), db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
#     check_object_ownership()

#     avatar_in = schemas.AvatarIn(filename=file.filename)
#     avatar = await crud.create_group_avatar(db, avatar_in, profile, file)

#     return avatar

@router.put('/avatar/', response_model=schemas.Avatar)
async def update_group_avatar(file: UploadFile = Form(...), db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    avatar_in = schemas.AvatarIn(filename=file.filename)
    avatar = await crud.update_group_avatar(db, avatar_in, profile.group, file)

    return avatar

@router.delete('/avatar/')
async def delete_group_avatar(db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    crud.delete_group_avatar(db, profile)

    return {
        'detail': 'Successfully deleted profile avatar'
    }