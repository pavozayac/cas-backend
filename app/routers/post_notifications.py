from app.dependencies import LoginAuth, get_database
from fastapi import APIRouter
from fastapi.param_functions import Depends
from pydantic.types import SecretBytes
from ..resources import crud, schemas, models
from sqlalchemy.orm.session import Session  

router = APIRouter()

#Testing route
@router.post('', response_model=schemas.Notification)
async def post_notification(notification: schemas.NotificationIn, db: Session = Depends(get_database)):
    notification = crud.create_notification(db, notification)
    return notification