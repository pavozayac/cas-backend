from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.sql.schema import CheckConstraint
from ..dependencies import LoginAuth, ModeratorAuth, get_database
from ..utils import check_object_ownership, filter_from_schema, sort_from_schema, check_access_from_visibility
from ..resources import schemas, models, crud
from sqlalchemy.orm.session import Session

from typing import List, Optional

router = APIRouter()

@router.get('/reflections/query', response_model=List[schemas.ReflectionReport])
async def get_reflection_reports(db: Session = Depends(get_database), profile: models.Profile = Depends(ModeratorAuth)):
    return crud.read_reflection_reports(db)

@router.get('/comment/query', response_model=List[schemas.CommentReport])
async def get_comment_reports(db: Session = Depends(get_database), profile: models.Profile = Depends(ModeratorAuth)):
    return crud.read_comment_reports(db)