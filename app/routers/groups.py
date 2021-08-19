from fastapi import APIRouter, UploadFile, Form
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse
from pydantic.schema import schema
from sqlalchemy.orm.session import Session
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from ..resources import crud, schemas, models
from ..dependencies import get_database, LoginAuth
from ..utils import check_object_ownership, sort_from_schema, filter_from_schema
from typing import List, Optional

router = APIRouter()

#
#   Advanced queries for groups
#

@router.post('/query', response_model=List[schemas.Group])
async def filter_groups(filters: schemas.GroupFilters, sorts: schemas.GroupSorts, db: Session = Depends(get_database)):
    return crud.filter_groups(db, filters, sorts)

#
#   CRUD for groups
#

@router.post('/', response_model=schemas.Group)
async def add_group(group: schemas.GroupIn, db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    return crud.create_group(db, group, profile.id)

@router.get('/{id}', response_model=schemas.Group)
async def get_group(id: int, db: Session = Depends(get_database)):
    return crud.read_group_by_id(db, id)

@router.put('/{id}', response_model=schemas.Group)
async def put_group(id: int, data: schemas.GroupIn, db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    group = crud.read_group_by_id(db, id)
    check_object_ownership(group, 'coordinator_id', profile)

    return crud.update_group(db, group, data)


@router.delete('/{id}')
async def delete_group(id: int, db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    group = crud.read_group_by_id(db, id)
    check_object_ownership(group, 'coordinator_id', profile)
    crud.delete_group(db, group)

    return {
        'detail': 'Successfully deleted the group'
    }

#
#   CRUD and additional actions for join requests
#

@router.get('/{id}/join-requests', response_model=List[schemas.GroupJoinRequest])
async def get_join_requests(id: int, db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    group = crud.read_group_by_id(db, id)
    check_object_ownership(group, 'coordinator_id', profile)

    return group.group_requests

@router.post('/accept-request/{id}')
async def accept_group_join_request(id: int, db: Session = Depends(get_database)):
    request = crud.read_group_join_request_by_id(db, id)

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
    

@router.post('/deny-request/{id}')
async def deny_group_join_request(id: int, db: Session = Depends(get_database)):
    request = crud.read_group_join_request_by_id(db, id)

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
async def post_join_request(id: int, join_request: schemas.GroupJoinRequestIn, db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    if profile.group_id is not None:
        raise HTTPException(HTTP_409_CONFLICT, 'In order to send a join request you need to leave the current group.')

    group = crud.read_group_by_id(db, id)

    if group is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Not group with such id exists.')

    return crud.create_group_join_request(db, profile, join_request)



#
#   CRUD for avatar
#

@router.get('/avatar/{id}')
async def get_avatar_by_id(id: str, db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    avatar = crud.read_group_avatar(db, id)
    print(avatar.saved_path)

    return FileResponse(avatar.saved_path)

@router.post('/avatar', response_model=schemas.Avatar)
async def add_group_avatar(file: UploadFile = Form(...), db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    check_object_ownership()

    avatar_in = schemas.AvatarIn(filename=file.filename)
    avatar = await crud.create_group_avatar(db, avatar_in, profile, file)

    return avatar

@router.put('/avatar', response_model=schemas.Avatar)
async def update_group_avatar(file: UploadFile = Form(...), db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    avatar_in = schemas.AvatarIn(filename=file.filename)
    avatar = await crud.update_group_avatar(db, avatar_in, profile, file)

    return avatar

@router.delete('/avatar')
async def delete_group_avatar(db: Session = Depends(get_database), profile: models.Profile = Depends(LoginAuth)):
    crud.delete_group_avatar(db, profile)

    return {
        'detail': 'Successfully deleted profile avatar'
    }