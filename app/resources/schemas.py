from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr, validator, ValidationError
from datetime import date


#
# Profile schemas
#

class ProfileBase(BaseModel):
    first_name: str
    last_name: str
    post_visibility: int

    @validator('post_visibility')
    def visibility_validation(cls, v):
        if v < 0 or v > 2:
            raise ValidationError('Post visibility not within range')
        return v

class ProfileIn(ProfileBase):
    pass

#for adding moderators or admins
class SuperProfileIn(ProfileBase):
    is_admin: bool  
    is_moderator: bool


class Profile(ProfileBase):
    id: int
    group_id: Optional[int]
    date_joined: date
    post_visibility: int

    class Config:
        orm_mode = True

class ProfileFilters(BaseModel):
    group_id: Optional[int]
    post_visibility: Optional[int]
    last_online_gte: Optional[date]
    last_online_lte: Optional[date]
    date_joined_gte: Optional[date]
    date_joined_lte: Optional[date]

class ProfileSorts(BaseModel):
    date_joined: Optional[str]
    post_visibility: Optional[str]
    last_online: Optional[str]
    first_name: Optional[str]
#
# BasicLogin schemas
#

class BasicLoginBase(BaseModel):
    email: EmailStr
   

class BasicLoginIn(BasicLoginBase):
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
#   Registration scheme
#

class RegisterIn(ProfileIn,  BasicLoginIn):
    pass

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

#
#   Group schemas
#

class GroupBase(BaseModel):
    coordinator_id: int
    name: str
    graduation_year: int

class GroupIn(GroupBase):
    pass

class Group(GroupBase):
    date_created: date

#
#   GroupJoinRequests
#

# No profile_id because it is set from profile received in auth dependency
class GroupJoinRequestBase(BaseModel):
    group_id: int

class GroupJoinRequestIn(GroupJoinRequestBase):
    pass

class GroupJoinRequest(GroupJoinRequestBase):
    profile_id: int
    date_added: date
    
#
#   Notifications
#

class NotificationBase(BaseModel):
    content: str

class NotificationIn(NotificationBase):
    recipients: List[int]

class Notification(NotificationBase):
    date_sent: date

    class Config:
        orm_mode = True

#
#   Attachments
#

class AttachmentBase(BaseModel):
    reflection_id: int
    filename: int

class AttachmentIn(AttachmentBase):
    pass

class Attachment(AttachmentBase):
    saved_path: str
    date_added: date

#
#   Reflections
#

class ReflectionBase(BaseModel):
    title: str
    text_content: str
    creativity: bool
    activity: bool
    service: bool

class ReflectionIn(ReflectionBase):
    pass

class Reflection(ReflectionBase):
    profile_id: int
    slug: str
    date_added: date

#
#   Tags
#   

class TagBase(BaseModel):
    name: str

class TagIn(TagBase):
    pass

class Tag(TagBase):
    date_added: date

#
#   Comments
#

class CommentBase(BaseModel):
    content: int

class CommentIn(CommentBase):
    pass

class Comment(CommentBase):
    profile_id: int
    reflection_id: int
    date_added: date

#
#   Reflection reports
#

class ReflectionReportBase(BaseModel):
    reason: str

class ReflectionReportIn(ReflectionReportBase):
    pass

class ReflectionReport(ReflectionReportBase):
    reflection_id: int
    date_added: date

#
#   Comment reports
#

class CommentReportBase(BaseModel):
    comment_id: int
    reason: str

class CommentReportIn(CommentReportBase):
    pass

class CommentReport(CommentReportBase):
    date_added: date