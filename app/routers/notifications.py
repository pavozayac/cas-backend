from starlette.status import HTTP_401_UNAUTHORIZED
from ..database import Database
from .auth import LoginAuth
from fastapi import APIRouter, HTTPException, Form
from fastapi.param_functions import Depends
from pydantic.types import SecretBytes
from ..resources import crud, schemas, models
from ..utils import check_object_ownership
from sqlalchemy.orm.session import Session  
from typing import List

router = APIRouter()

#Testing route
@router.post('', response_model=schemas.Notification)
async def post_notification(notification: schemas.NotificationIn, db: Session = Depends(Database), coordinator: models.Profile = Depends(LoginAuth)):
    if not coordinator.is_admin and not coordinator.is_moderator:
        for id in notification.recipients:
            recipient = crud.read_profile_by_id(db, id)           

            if recipient.group.coordinator.id != coordinator.id:
                raise HTTPException(HTTP_401_UNAUTHORIZED, 'Invalid recipients')

    return crud.create_notification(db, notification)

@router.get('/query', response_model=List[schemas.Notification])
async def filter_posted_notifications(sorts: schemas.NotificationSorts, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    return crud.filter_authored_notifications(db, profile, sorts)

@router.delete('/{id}')
async def delete_notification(id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    notification = crud.read_notification_by_id(db, id)

    check_object_ownership(notification, 'profile_id', profile)

    crud.delete_notification(db, notification)

    return {
        'detail': 'Successfully deleted notification'
    }