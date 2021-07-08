from typing import Any, Dict
from fastapi import HTTPException, status
from pydantic import BaseModel
from .resources.models import Profile
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc

#
#   This is here to avoid circular imports
#

def CREDENTIALS_EXCEPTION(detail = 'Invalid credentials'):
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail=detail
    )

def check_object_ownership(object, profile: Profile):
    if object.profile_id != profile.id:
        raise CREDENTIALS_EXCEPTION('Invalid onwership')


def filter_from_schema(query: Query, model, schema: BaseModel):
    cleaned: Dict[str, Any] = {k: v for k, v in schema.dict().items() if v is not None}

    for k, v in cleaned.items():
        if '_gte' in k:
            query = query.filter(getattr(model, k[:len(k)-4]) <= v)
        elif '_lte' in k:
            query = query.filter(getattr(model, k[:len(k)-4]) >= v)
        else:
            query = query.filter(getattr(model, k) == v)


    return query

def sort_from_schema(query: Query, model, schema: BaseModel):
    cleaned: Dict[str, Any] = {k: v for k, v in schema.dict().items() if v is not None}

    for k, v in cleaned.items():
        if v == 'asc':
            query = query.order_by(asc(getattr(model, k)))
        else: #v == 'desc' in k:
            query = query.order_by(desc(getattr(model, k)))

    return query
