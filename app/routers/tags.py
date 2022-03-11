from fastapi import APIRouter, Depends
from sqlalchemy.sql.schema import CheckConstraint
from ..database import Database
from .auth import AdminAuth, LoginAuth
from ..utils import check_object_ownership, filter_from_schema, sort_from_schema, check_access_from_visibility
from ..resources import schemas, models, crud
from sqlalchemy.orm.session import Session

from typing import List, Optional

router = APIRouter()

@router.get('/', response_model=List[schemas.Tag])
async def get_all_tags(db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    return crud.read_tags(db)


@router.delete('/{name}')
async def delete_tag(name: str, db: Session = Depends(Database), profile: models.Profile = Depends(AdminAuth)):
    tag = crud.read_tag_by_name(db, name)
    crud.delete_tag(db, tag)

    return {
        'detail': 'Tag deleted successfully'
    }