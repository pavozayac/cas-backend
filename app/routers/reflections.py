from sre_constants import LITERAL_IGNORE
from fastapi import APIRouter, Depends
from fastapi.datastructures import UploadFile
from fastapi.exceptions import HTTPException
from fastapi.param_functions import File
from sqlalchemy.sql.schema import CheckConstraint
from ..utils import check_object_ownership, filter_from_schema, sort_from_schema, check_access_from_visibility
from ..resources import schemas, models, crud
from sqlalchemy.orm.session import Session
from fastapi.responses import FileResponse
from ..database import Database
from .auth import LoginAuth

from typing import List, Optional

router = APIRouter()

#
#   Queries, that is advanced search and filtering, sorting
#

@router.post('/query', response_model=List[schemas.Reflection])
async def filter_reflections(filters: schemas.ReflectionFilters, sorts: schemas.ReflectionSorts, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflections = crud.filter_reflections(db, filters, sorts, profile)
    for reflection in reflections:
        try:
            check_access_from_visibility(reflection, profile)
        except HTTPException:
            reflections.remove(reflection)

    return reflections

@router.post('/favourites', response_model=List[schemas.Reflection])
async def favourite_reflections(filters: schemas.ReflectionFilters, sorts: schemas.ReflectionSorts, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflections = crud.filter_favourite_reflections(db, filters, sorts, profile)

    for reflection in reflections:
        try:
            check_access_from_visibility(reflection, profile)
        except HTTPException:
            reflections.remove(reflection)

    return reflections
#   
#   CRUD actions for reflections
#

@router.post('/', response_model=schemas.Reflection)
async def post_reflection(reflection: schemas.ReflectionIn, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    return crud.create_reflection(db, profile.id, reflection)

@router.get('/{id}', response_model=schemas.Reflection)
async def get_reflection_by_id(id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)
    print(reflection.tags)

    check_access_from_visibility(reflection, profile)

    return reflection

@router.put('/{id}', response_model=schemas.Reflection)
async def update_reflection(id: int, data: schemas.ReflectionIn, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)

    check_object_ownership(reflection, profile, 'profile_id')

    return crud.update_reflection(db, reflection, data)

@router.delete('/{id}')
async def delete_reflection(id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)

    check_object_ownership(reflection, profile, 'profile_id')

    crud.delete_reflection(db, reflection)

    return {
        'detail': 'Successfully deleted reflection'
    }

#
#   Advanced queries for comments
#

@router.post('/{id}/comments/query', response_model=List[schemas.Comment])
async def get_reflection_comments(id: int, sorts: schemas.CommentSorts, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)

    check_access_from_visibility(reflection, profile)

    return crud.filter_reflection_comments(db, id, sorts)

#
#   CRUD actions for comments
#

@router.post('/{id}/comments', response_model=schemas.Comment)
async def post_comment(id: int, comment: schemas.CommentIn, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)

    check_access_from_visibility(reflection, profile)

    return crud.create_comment(db, profile.id, reflection.id, comment)



@router.get('/{reflection_id}/comments/{comment_id}', response_model=schemas.Comment)
async def get_comment_by_id(reflection_id: int, comment_id: int, db: Session = Depends(Database), profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, reflection_id, profile)

    check_access_from_visibility(reflection, profile)

    return crud.read_comment_by_id(db, comment_id)

@router.delete('/{reflection_id}/comments/{comment_id}')
async def delete_comment(comment_id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    comment = crud.read_comment_by_id(db, comment_id)

    check_object_ownership(comment, 'profile_id', profile)

    crud.delete_comment(db, comment)

    return {
        'detail': 'Successfully deleted comment'
    }

#
#   Favourites actions
#

@router.post('/{reflection_id}/favourite')
async def favourite_reflection(reflection_id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, reflection_id, profile)

    check_access_from_visibility(reflection, profile)

    crud.create_favourite(db, reflection, profile)

    return {
        'detail': 'Successfully favourited reflection'
    }
    

    
@router.delete('/{reflection_id}/favourite')
async def unfavourite_reflection(reflection_id: int, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, reflection_id, profile)

    check_access_from_visibility(reflection, profile)

    crud.delete_favourite(db, reflection, profile)
    
    return {
        'detail': 'Successfully unfavourited reflection'
    }

#
#   Attachments CRUD
#

@router.get('/{id}/attachment/{uuid}')
async def get_attachment(id: int, uuid: str, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)
    check_access_from_visibility(reflection, profile)

    attachment = crud.read_reflection_attachment(db, uuid)

    return FileResponse(attachment.saved_path)


@router.post('/{id}/attachment', response_model=schemas.Attachment)
async def add_attachment(id: int, file: UploadFile = File(...), db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)
    check_object_ownership(reflection, profile)

    attachment_in = schemas.AttachmentIn(
        reflection_id=id,
        filename=file.filename
    )

    attachment = await crud.create_reflection_attachment(db, attachment_in, file)

    return attachment

@router.delete('/{id}/attachment/{uuid}')
async def delete_attachment(id: int, uuid: str, db: Session = Depends(Database), profile: models.Profile = Depends(LoginAuth)):
    reflection = crud.read_reflection_by_id(db, id, profile)
    check_object_ownership(reflection, profile)

    attachment = crud.read_reflection_attachment(db, uuid)
    crud.delete_reflection_attachment(db, attachment)

    return {
        'detail': 'Successfully deleted reflection attachment'
    }
