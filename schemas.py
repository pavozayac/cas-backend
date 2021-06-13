from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr
from datetime import date

#
# Profile schemas
#
class ProfileBase(BaseModel):
    first_name: str
    last_name: str
    post_visibility: int = Field(gt=-1, lt=3)
    group_id: int

class ProfileIn(ProfileBase):
    pass

#for adding moderators or admins
class SuperProfileIn(ProfileBase):
    is_admin: bool
    is_moderator: bool

class Profile(ProfileBase):
    id: int

    class Config:
        orm_mode = True

#
# BasicLogin schemas
#
class BasicLoginBase(BaseModel):
    profile_id: int
    email: EmailStr
    verification_sent: bool
    verified: bool

class BasicLoginIn(BasicLoginBase):
    password: str
    

class BasicLogin(BasicLoginBase):
    pass

    class Config:
        orm_mode = True

#
#   ForeignLogin schemas
#
class ForeignLoginBase(BaseModel):
    profile_id: int
    access_token: str
    expires_at: date
    method: str

class ForeignLoginIn(ForeignLoginBase):
    pass

class ForeignLogin(ForeignLoginBase):
    pass

    class Config:
        orm_mode = True