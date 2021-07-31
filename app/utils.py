from typing import Any, Dict, Type
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

def check_object_ownership(object, field: str, profile: Profile):
    if getattr(object, field) != profile.id:
        raise CREDENTIALS_EXCEPTION('Invalid onwership')


def filter_from_schema(query: Query, model, schema: BaseModel):
    cleaned: Dict[str, Any] = {
        k: v 
        for k, v in schema.dict().items() 
        if v is not None
    }

    for k, v in cleaned.items():
        if isinstance(v, dict):
            v = {
                sub_key: sub_value
                for sub_key, sub_value in v.dict().items()
                if sub_value is not None
            }
    
    for k, v in cleaned.items():
        if '_gte' in k:
            query = query.filter(getattr(model, k[:len(k)-4]) <= v)
        elif '_lte' in k:
            query = query.filter(getattr(model, k[:len(k)-4]) >= v)
        #elif isinstance(v, dict):
        #    for sub_key, sub_value in v.items():
        #        query = query.filter(getattr)
        else:
            query = query.filter(getattr(model, k) == v)

    for k, v in cleaned.items():
        if '_gte' in k:
            query = query.filter(k[:len(k)-4] <= v)
        elif '_lte' in k:
            query = query.filter(k[:len(k)-4] >= v)
        #elif isinstance(v, dict):
        #    for sub_key, sub_value in v.items():
        #        query = query.filter(getattr)
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
