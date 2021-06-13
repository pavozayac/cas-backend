from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Integer, Enum
from sqlalchemy.orm import relationship, backref

from .database import Base



class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_joined = Column(Date)
    # 0 = only coordinator, 1 = only group, 2 = everyone
    post_visibility = Column(Integer)
    last_online = Column(Date)
    is_moderator = Column(Boolean)
    is_admin = Column(Boolean)

    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    group = relationship('Group', backref=backref('profiles', uselist=False), foreign_keys=[group_id])

    basic_login = relationship('BasicLogin')

class BasicLogin(Base):
    __tablename__ = 'basic_logins'

    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)

    email = Column(String(100), unique=True)
    password = Column(String)
    verification_sent = Column(Boolean)
    verified = Column(Boolean)

class ForeignLogin(Base):
    __tablename__ = 'foreign_logins'

    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)

    access_token = Column(String)
    expires_at = Column(Date)
    # method = through Google or Facebook
    method = Column(String)


class Group(Base):
    __tablename__ = 'groups'

    id = Column(String(10), primary_key=True)

    coordinator_id = Column(Integer, ForeignKey('profiles.id'))
    coordinator = relationship('Profile', backref=backref('owned_group', uselist=False), foreign_keys=[coordinator_id])

    name = Column(String)
    graduation_year = Column(Integer)
    date_created = Column(Date)
