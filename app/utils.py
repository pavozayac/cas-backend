from typing import Any, Dict, Type
from fastapi import HTTPException, status
from fastapi.datastructures import UploadFile
from pydantic import BaseModel
import sqlalchemy
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc
from starlette.status import HTTP_401_UNAUTHORIZED
from .resources import models, schemas
from app import settings
import aiofiles
from uuid import uuid4 as uuid
from os import remove
from datetime import datetime

#
#   This is here to avoid circular imports
#

def CREDENTIALS_EXCEPTION(detail = 'Invalid credentials'):
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail=detail
    )

def check_object_ownership(object, profile: models.Profile, field: str = 'profile_id'):
    if getattr(object, field) != profile.id and not profile.is_moderator and not profile.is_admin:
        raise CREDENTIALS_EXCEPTION('Invalid ownership')



def check_access_from_visibility(reflection: models.Reflection, profile: models.Profile):
    if reflection.author.post_visibility == 0:
        print(1)
        if profile.id != reflection.profile_id and not profile.is_admin and not profile.is_moderator and profile != reflection.author.group.coordinator:
            raise CREDENTIALS_EXCEPTION('Unauthorized access')

    elif reflection.author.post_visibility == 1:
        if profile.id != reflection.profile_id \
            and not profile.is_admin and not profile.is_moderator and profile != reflection.author.group.coordinator \
            and profile.group.id != reflection.author.group_id:
            raise CREDENTIALS_EXCEPTION('Unauthorized access')

def filter_from_schema(query: Query, schema: BaseModel):
    cleaned: Dict[str, Any] = {
        k: v
        for k, v in schema.dict().items()
        if v is not None
    }

    
    for k, v in cleaned.items():
        if '_gte' in k:
            query = query.filter(getattr(schema.Meta.source, k[:len(k)-4]) <= v)
        elif '_lte' in k:
            query = query.filter(getattr(schema.Meta.source, k[:len(k)-4]) >= v)
        elif isinstance(v, dict):
            print('Found instance of the BaseModel')
            cleaned_subquery = {
                sub_key: sub_value
                for sub_key, sub_value in v.items()
                if sub_value is not None
            }

            for sub_key, sub_value in cleaned_subquery.items():
                if '_gte' in sub_key:
                    query = query.join(getattr(schema, k).Meta.source, aliased=True).filter(getattr(getattr(schema, k).Meta.source, sub_key[:len(sub_key)-4]) <= sub_value)
                elif '_lte' in sub_key:
                    query = query.join(getattr(schema, k).Meta.source, aliased=True).filter(getattr(getattr(schema, k).Meta.source, sub_key[:len(sub_key)-4]) >= sub_value)
                else:
                    query = query.join(getattr(schema, k).Meta.source, aliased=True).filter_by(**{
                        sub_key: sub_value
                    })
        else:
            query = query.filter(getattr(schema.Meta.source, k) == v)

    return query

def sort_from_schema(query: Query, schema: BaseModel):
    cleaned: Dict[str, Any] = {k: v for k, v in schema.dict().items() if v is not None}

    print(cleaned.items())


    for k, v in cleaned.items():
        if v == 'asc':
            query = query.order_by(asc(getattr(schema.Meta.source, k)))
        else: #v == 'desc' in k:
            query = query.order_by(desc(getattr(schema.Meta.source, k)))

    return query


async def save_generic_attachment(file: UploadFile):
    id = uuid()

    generated_path = settings.ATTACHMENT_PATH + str(id) + '.' + file.filename.split('.')[-1]

    async with aiofiles.open(generated_path, 'wb') as aio_file:
        content = await file.read()
        await aio_file.write(content)

    return generated_path, id

async def delete_generic_attachment(object):
    if not hasattr(object, 'saved_path'):
        raise 'Invalid object'

    remove(getattr(object, 'saved_path'))