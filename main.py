from sqlalchemy.orm.session import Session

from fastapi import FastAPI, Depends, HTTPException
from .schemas import BasicLoginIn
from .database import SessionLocal, engine
from .dependencies import get_database

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.get('/{id}')
async def root(id: int):
    return {'Returned id': id}

@app.get('/auth/basic/{email}', response_model=schemas.BasicLogin)
async def get_basic(email: str, db: Session = Depends(get_database)):
    basic_login = crud.get_basic_login_by_email(db, email)
    if basic_login is None:
        raise HTTPException(status_code=404, detail='Basic login not found')
    return basic_login


@app.post('/auth/register')
async def register(login: BasicLoginIn, db: Session = Depends(get_database)):
    crud.create_basic_login(db, login)

