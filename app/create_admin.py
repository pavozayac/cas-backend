from datetime import date

from pydantic import ValidationError
from app.resources import models
from app.database import Database
from app.routers.auth import password_context
from app.resources.schemas import BasicLoginIn, ProfileIn

incomplete = True

while incomplete:
    first_name = input('First name: ')
    last_name = input('Last name: ')

    try:
        ProfileIn(
            first_name=first_name,
            last_name=last_name
        )
    except ValidationError: 
        print('Validation error.')
        continue

    email = input('Email: ')
    password = input('Password: ')

    try:
        BasicLoginIn(
            email=email,
            password=password
        )
    except ValidationError:
        print('Validation error.')
        continue

    incomplete = False



with Database() as db:
    profile_obj = models.Profile(
        first_name=first_name,
        last_name=last_name,
        is_moderator=True,
        is_admin=True,
        date_joined=date.today(),
        last_online=date.today()
    )

    db.add(profile_obj)
    db.commit()
    db.refresh(profile_obj)

    basic_obj = models.BasicLogin(
        profile_id=profile_obj.id,
        email=email,
        password=password_context.hash(password),
        verification_sent=False,
        verified=False
    )

    db.add(basic_obj)
    db.commit()
    db.refresh(basic_obj)
