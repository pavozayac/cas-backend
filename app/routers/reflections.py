from fastapi import APIRouter, Depends
from ..dependencies import LoginAuth, get_database
from ..utils import filter_from_schema, sort_from_schema
from ..resources import schemas, models, crud

router = APIRouter()

@router.get('/')
async def filter_reflections(filters, sorts, db: Session = Depends(get_database)):
    

