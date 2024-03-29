from app.database import Base
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr, validator, ValidationError, root_validator
from datetime import date, datetime
from ..resources import models

# 
#   Group sorts moved here to be used by ProfileSorts
# 

class GroupSorts(BaseModel):
    date_created: Optional[str]
    name: Optional[str]
    graduation_year: Optional[str]

    class Meta:
        source = models.Group

#
#   Pagination
#

class Pagination(BaseModel):
    limit: Optional[int]
    page: Optional[int]
 
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
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    # post_visibility: int

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
    # post_visibility: int
    avatar: Optional[Avatar]
    reflections_count: int
    graduation_year: Optional[int]
    is_admin: bool

    class Config:
        orm_mode = True

class ProfileFilters(BaseModel):
    id: Optional[int]
    group_id: Optional[str]
    last_online_gte: Optional[date]
    last_online_lte: Optional[date]
    date_joined_gte: Optional[date]
    date_joined_lte: Optional[date]
    full_text_con: Optional[str]

    class Meta:
        source = models.Profile

class ProfileSorts(BaseModel):
    date_joined: Optional[str]
    last_online: Optional[str]
    first_name: Optional[str]
    graduation_year: Optional[str]

    class Meta:
        source = models.Profile

class BulkProfile(BaseModel):
    id: int

    class Config:
        orm_mode = True

class BulkProfileResponse(BaseModel):
    items: List[BulkProfile]
    count: int

#
#   BasicLogin schemas
#

class BasicLoginBase(BaseModel):
    email: EmailStr

    @validator('email')
    def email_length(cls, v):
        if len(v) > 100:
            raise ValidationError('Email cannot be longer than 100 characters.')

        return v

class BasicLoginIn(BasicLoginBase):
    password: str = Field(..., max_length=100)

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
    email: EmailStr

    @validator('email')
    def email_length(cls, v):
        if len(v) > 100:
            raise ValidationError('Email cannot be longer than 100 characters.')

        return v


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
    name: str = Field(..., max_length=255)
    description: str = Field(..., max_length=1000)
    graduation_year: int = Field(lt=date.today().year+3, gt=date.today().year-1)

class GroupIn(GroupBase):
    pass

class BulkGroup(BaseModel):
    id: str

    class Config:
        orm_mode = True

class BulkGroupResponse(BaseModel):
    items: List[BulkGroup]
    count: int

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
    full_text_con: Optional[str]

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
    content: str = Field(..., max_length=200)

class NotificationIn(NotificationBase):
    recipients: List[int]

class Notification(NotificationBase):
    date_sent: date
    read: bool

    class Config:
        orm_mode = True

class BulkNotificationRecipient(BaseModel):
    profile_id: int

    class Config:
        orm_mode = True

class NotificationNoRead(NotificationBase):
    date_sent: date
    notification_recipients: List[BulkNotificationRecipient]

    class Config:
        orm_mode = True

class NotificationSorts(BaseModel):
    date_sent: Optional[str]
    read_omit: Optional[str]

    class Meta:
        source = models.Notification

class NotificationFilters(BaseModel):
    read: Optional[bool]
    # notification_recipients_con: Optional[int]
    # author: Optional[int]
    class Meta:
        source = models.Notification

class BulkNotification(BaseModel):
    id: int

    class Config:
        orm_mode = True

class BulkNotificationResponse(BaseModel):
    items: List[BulkNotification]
    count: int
    read_count: int

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
    content: str = Field(..., max_length=200)

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

class BulkCommentResponse(BaseModel):
    items: List[BulkComment]
    count: int

# Comments cannot be filtered, as basic filtering functionality is provided via the URL (retrieving comments from under a single reflection)
class CommentSorts(BaseModel):
    date_added: Optional[str]

    class Meta:
        source = models.Comment

#
#   Reflections
#

class ReflectionBase(BaseModel):
    title: str = Field(..., max_length=100)
    text_content: str = Field(..., max_length=5000)
    creativity: bool
    activity: bool
    service: bool
    post_visibility: int

    @validator('post_visibility')
    def visibility_validation(cls, v):
        if v not in [0,1,2]:
            raise ValidationError('Post visibility not within range')
        return v


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

class BulkReflectionResponse(BaseModel):
    items: List[BulkReflection]
    count: int

class ReflectionFilters(BaseModel):
    title: Optional[str]
    creativity: Optional[bool]
    activity: Optional[bool]
    service: Optional[bool]
    profile: Optional[ProfileFilters]
    post_visibility: Optional[int]
    date_added_gte: Optional[date]
    date_added_lte: Optional[date]
    full_text_con: Optional[str]

    class Meta:
        source = models.Reflection

class ReflectionSorts(BaseModel):
    title: Optional[str]
    post_visibility: Optional[int]
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