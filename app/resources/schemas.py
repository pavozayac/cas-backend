from app.database import Base
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr, validator, ValidationError, root_validator
from datetime import date, datetime
from ..resources import models
 
#
#   Attachments
#

class AttachmentBase(BaseModel):
    reflection_id: int
    filename: str

class AttachmentIn(AttachmentBase):
    pass

class Attachment(AttachmentBase):
    id: str 
    saved_path: str
    date_added: date

    class Config:
        orm_mode = True

#
#   Generic Avatar Schemas
#

class AvatarBase(BaseModel):
    filename: str

class AvatarIn(AvatarBase):
    pass

class Avatar(AvatarBase):
    id: str
    saved_path: str
    date_added: date

    class Config:
        orm_mode = True


#
# Profile schemas
#

class ProfileBase(BaseModel):
    first_name: str
    last_name: str
    post_visibility: int

    @validator('post_visibility')
    def visibility_validation(cls, v):
        if v not in [0,1,2]:
            raise ValidationError('Post visibility not within range')
        return v

class ProfileIn(ProfileBase):
    pass

#for adding moderators or admins
class SuperProfileIn(ProfileBase):
    is_admin: bool  
    is_moderator: bool

class BulkProfile(BaseModel):
    id: int

    class Config:
        orm_mode = True

class Profile(ProfileBase):
    id: int
    group_id: Optional[str]
    date_joined: date
    post_visibility: int
    avatar: Optional[Avatar]
    reflections_count: int

    class Config:
        orm_mode = True

class ProfileFilters(BaseModel):
    id: Optional[int]
    group_id: Optional[str]
    post_visibility: Optional[int]
    last_online_gte: Optional[date]
    last_online_lte: Optional[date]
    date_joined_gte: Optional[date]
    date_joined_lte: Optional[date]

    class Meta:
        source = models.Profile

class ProfileSorts(BaseModel):
    date_joined: Optional[str]
    post_visibility: Optional[str]
    last_online: Optional[str]
    first_name: Optional[str]

    class Meta:
        source = models.Profile

#
#   BasicLogin schemas
#

class BasicLoginBase(BaseModel):
    email: EmailStr

class BasicLoginIn(BasicLoginBase):
    password: str

    @validator('password')
    def password_validator(cls, value: str):
        try:
            assert len(value) >= 8
        except AssertionError:
            raise ValueError('Password too short')
        try:
            assert any(character.isdigit() for character in value)
        except AssertionError:
            raise ValueError('Password must contain at least 1 digit')
        try:
            assert any(character.isupper() for character in value)
        except AssertionError:
            raise ValueError('Password must contain at least 1 capital character')

        return value

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
#   Sending recovery mail schema
#

class SendRecoveryMailSchema(BaseModel):
    email: str

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
    access_token: str
    token_type: str

#
#   Group schemas
#

class GroupBase(BaseModel):
    name: str
    description: str
    graduation_year: int

class GroupIn(GroupBase):
    pass

class BulkGroup(BaseModel):
    id: str

    class Config:
        orm_mode = True

class Group(GroupBase):
    id: str
    coordinator_id: int
    date_created: date
    avatar: Optional[Avatar]
    members_count: int
    reflections_count: int

    class Config:
        orm_mode = True

class GroupFilters(BaseModel):
    coordinator_id: Optional[int]
    name: Optional[str]
    date_created_gte: Optional[date]
    date_created_lte: Optional[date]

    class Meta:
        source = models.Group

class GroupSorts(BaseModel):
    date_created: Optional[str]
    name: Optional[str]

    class Meta:
        source = models.Group

#
#   GroupJoinRequests
#

# No profile_id because it is set from profile received in auth dependency
# class GroupJoinRequestBase(BaseModel):
#     group_id: int

# class GroupJoinRequestIn(GroupJoinRequestBase):
#     pass

class GroupJoinRequest(BaseModel):
    group_id: str
    profile: Profile
    date_added: date

    class Config:
        orm_mode = True
    
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

class NotificationSorts(BaseModel):
    date_sent: Optional[str]

#
#   Tags
#   

class TagBase(BaseModel):
    name: str

class TagIn(TagBase):
    pass

class Tag(TagBase):
    date_added: date

    class Config:
        orm_mode = True

class TagFilters(BaseModel):
    name: Optional[str]

    class Meta:
        source = models.Tag

class TagSorts(BaseModel):
    name: Optional[str] 
    date_added: Optional[str]

#
#   Comments
#

class CommentBase(BaseModel):
    content: str

class CommentIn(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    profile_id: int
    reflection_id: int
    date_added: date

    class Config:
        orm_mode = True

class BulkComment(BaseModel):
    id: int

    class Config:
        orm_mode = True

# Comments cannot be filtered, as basic filtering functionality is provided via the URL (retrieving comments from under a single reflection)
class CommentSorts(BaseModel):
    date_added: Optional[str]

    class Meta:
        source = models.Comment

#
#   Reflections
#

class ReflectionBase(BaseModel):
    title: str
    text_content: str
    creativity: bool
    activity: bool
    service: bool

    @root_validator
    def validate_categories(cls, values):
        cats = [values['creativity'], values['activity'], values['service']]
        try:
            assert any(cats)
        except:
            raise ValueError('At least one category must be true')
        return values
    

class ReflectionIn(ReflectionBase):
    tags: List[TagIn]

class Reflection(ReflectionBase):
    id: int
    profile_id: int
    slug: str
    date_added: date
    is_favourite: bool
    comments: List[BulkComment]
    tags: List[Tag]
    attachments: List[Attachment]
    # Warning, this property needs to be set explicitly in the routes, as it requires info about the user

    class Config:
        orm_mode = True

class BulkReflection(BaseModel):
    id: int

    class Config:
        orm_mode = True

class ReflectionFilters(BaseModel):
    title: Optional[str]
    creativity: Optional[bool]
    activity: Optional[bool]
    service: Optional[bool]
    profile: Optional[ProfileFilters]
    date_added_gte: Optional[date]
    date_added_lte: Optional[date]
    full_text_con: Optional[str]

    class Meta:
        source = models.Reflection

class ReflectionSorts(BaseModel):
    title: Optional[str]
    date_added: Optional[str]

    class Meta:
        source = models.Reflection

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

    class Config:
        orm_mode = True

class ReflectionReportSorts(BaseModel):
    date_added: Optional[str]

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

    class Config:
        orm_mode = True

class CommentReportSorts(BaseModel):
    date_added: Optional[str]

#
#   Message schemas
#

class MessageBase(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageIn(MessageBase):
    pass

class Message(MessageBase):
    id: int
    date_added: datetime

    class Config:
        orm_mode = True