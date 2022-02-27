from starlette.status import HTTP_401_UNAUTHORIZED
from ..database import Database
from .auth import AdminAuth, LoginAuth
from fastapi import APIRouter, HTTPException, Form
from fastapi.param_functions import Depends
from pydantic.types import SecretBytes
from ..resources import crud, schemas, models
from ..utils import check_object_ownership
from sqlalchemy.orm.session import Session  
from typing import List, Optional

router = APIRouter()

#Testing route
@router.post('', response_model=schemas.Notification)
async def post_notification(notification: schemas.NotificationIn, db: Session = Depends(Database), admin: models.Profile = Depends(AdminAuth)):
    # if not coordinator.is_admin and not coordinator.is_moderator:
    #     for id in notification.recipients:
    #         recipient = crud.read_profile_by_id(db, id)           

    #         if recipient.group.coordinator.id != coordinator.id:
    #             raise HTTPException(HTTP_401_UNAUTHORIZED, 'Invalid recipients')

    return crud.create_notification(db, notification)

@router.post('/received/query', response_model=schemas.BulkNotificationResponse)
async def filter_received_notifications(sorts: schemas.NotificationSorts, filters: schemas.NotificationFilters, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth), pagination: Optional[schemas.Pagination] = None):
    notifications, count = crud.filter_notifications_by_recipient(db, sorts, filters, pagination, profile.id)
    return schemas.BulkNotificationResponse(items=notifications, count=count)

@router.post('/posted/query', response_model=schemas.BulkNotificationResponse)
async def filter_posted_notifications(sorts: schemas.NotificationSorts, filters: schemas.NotificationFilters, db: Session = Depends(Database), profile: models.Profile = Depends(AdminAuth), pagination: Optional[schemas.Pagination] = None):
    notifications, count = crud.filter_authored_notifications(db, sorts, filters, pagination, profile.id)
    return schemas.BulkNotificationResponse(items=notifications, count=count)
    

@router.delete('/{id}')
async def delete_notification(id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    notification = crud.read_notification_by_id(db, id)

    check_object_ownership(notification, profile, 'profile_id')

    crud.delete_notification(db, notification)

    return {
        'detail': 'Successfully deleted notification'
    }