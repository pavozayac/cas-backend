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

class ProfileIn(ProfileBase):
    pass

#for adding moderators or admins
class SuperProfileIn(ProfileBase):
    is_admin: bool
    is_moderator: bool

class Profile(ProfileBase):
    id: int
    group_id: Optional[int]

    class Config:
        orm_mode = True

#
# BasicLogin schemas
#
class BasicLoginBase(BaseModel):
    email: EmailStr
   

class BasicLoginCreate(BasicLoginBase):
    profile_id: int
    password: str

class BasicLoginSignIn(BasicLoginBase):
    password: str
    

class BasicLogin(BasicLoginBase):
    password: str
    verification_sent: bool
    verified: bool

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

#
#   Auth
#

class Token(BaseModel):
    token: str
    token_type: str