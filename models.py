from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Integer, Enum
from sqlalchemy.orm import relationship

from database import Base

class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(String, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_joined = Column(Date)
    # 0 = only coordinator, 1 = only group, 2 = everyone
    post_visibility = Column(Integer)
    last_online = Column(Date)
    is_moderator = Column(Boolean)
    is_admin = Column(Boolean)

    group_id = relationship('Group', back_populates='profiles')

class BasicLogin(Base):
    __tablename__ = 'basic_logins'

    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)

    email = Column(String(100), unique=True)
    password = Column(String)
    verification_sent = Column(Boolean)
    verified = Column(Boolean)

class ForeignLogins(Base):
    __tablename__ = 'foreign_logins'

    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)

    access_token = Column(String)
    expires_at = Column(Date)
    # method = through Google or Facebook
    method = Column(String)


