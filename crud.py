from sqlalchemy.orm import Session
import schemas, models
from datetime import date
from passlib.context import CryptContext

#
#   Profile CRUD
#   

def create_profile(db: Session, profile: schemas.ProfileIn):
    profile_obj = models.Profile(
        first_name = profile.first_name,
        last_name = profile.last_name,
        date_joined = date.today(),
        last_online = date.today(),
        is_moderator = False,
        is_admin = False,
        group_id = None
    )

    db.add(profile_obj)
    db.commit()
    db.refresh(profile_obj)
    return profile_obj

def get_profile_by_id(db: Session, id: int):
    return db.query(models.Profile).filter(models.Profile.id == id).first()

def get_profile_by_email(db: Session, email: str):
    login = db.query(models.BasicLogin).filter(models.BasicLogin.email == email).first().profile_id
    return db.query(models.Profile).filter(models.Profile.id == login)

#
#   BasicLogin CRUD
#

password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def create_basic_login(db: Session, basic_login: schemas.BasicLoginIn):
    basic_obj = models.BasicLogin(
        profile_id = basic_login.profile_id,
        email = basic_login.email,
        password = password_context.hash(basic_login.password),
        verification_sent = False,
        verified = False
    )

    db.add(basic_obj)
    db.commit()

def get_basic_login_by_email(db: Session, email: str):
    return db.query(models.BasicLogin).filter(models.BasicLogin.email == email).first()
