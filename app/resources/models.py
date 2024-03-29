from datetime import datetime
from ntpath import realpath
from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Integer, Enum, DateTime, Table, Text, Unicode, event, JSON, VARCHAR, type_coerce
import sqlalchemy
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from os import remove as remove_file

from sqlalchemy.sql.functions import func
from sqlalchemy.ext.associationproxy import association_proxy

from ..database import Base


class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_joined = Column(Date)
    # 0 = only coordinator, 1 = only group, 2 = every logged in user, validation is provided in schemas
    last_online = Column(Date)
    # is_moderator = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    group_id = Column(String(10), ForeignKey('groups.id'), nullable=True)
    group = relationship('Group', back_populates='members', foreign_keys=[group_id])
    group_requests = relationship('GroupJoinRequest', back_populates='profile')

    notifications = relationship('NotificationRecipient', back_populates='recipient', cascade='all,delete')
    notifications_authored = relationship('Notification', back_populates='author', cascade='all,delete')

    reflections = relationship('Reflection', back_populates='author', cascade='delete')

    comments = relationship('Comment', back_populates='author', cascade='all,delete')

    favourited = relationship('Reflection', secondary='favourites', back_populates='favouritees')

    basic_login = relationship('BasicLogin', back_populates='profile', cascade='all,delete')
    foreign_login = relationship('ForeignLogin', back_populates='profile', cascade='all,delete')

    avatar_id = Column(VARCHAR(50), ForeignKey('profile_avatars.id'), nullable=True, default=None)
    avatar = relationship('ProfileAvatar', backref=backref('profile', uselist=False), cascade='all,delete')

    # sent_messages = relationship('Message', back_populates='sender', foreign_keys='[Message.sender_id]')
    # received_messages = relationship('Message', back_populates='receiver', foreign_keys='[Message.receiver_id]')

    @hybrid_property
    def reflections_count(self):
        return len(self.reflections)

    @hybrid_property
    def full_text(self):
        return self.first_name + self.last_name

    @hybrid_property
    def graduation_year(self):
        if self.group:
            return self.group.graduation_year
        else:
            return None

    @graduation_year.expression
    def graduation_year(cls):
        return (
            sqlalchemy.select(Group.graduation_year)
            .where(Group.id == cls.group_id)
            .label('graduation_year')
        )

#   This model will be used for profile pictures
class ProfileAvatar(Base):
    __tablename__ = 'profile_avatars'

    id = Column(VARCHAR(50), primary_key=True)

    saved_path = Column(String)
    filename = Column(String)
    date_added = Column(Date)

class BasicLogin(Base):
    __tablename__ = 'basic_logins'

    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)

    email = Column(String(100), unique=True)
    password = Column(String(100))
    verification_sent = Column(Boolean)
    verified = Column(Boolean)

    profile = relationship('Profile', back_populates='basic_login')

class ForeignLogin(Base):
    __tablename__ = 'foreign_logins'

    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)
    
    foreign_id = Column(String, primary_key=True)

    email = Column(String)
    #   This token is the token retrieved from the provider's OAuth service and includes data requested in scopes
    # Provider = through Google or Facebook
    provider = Column(String)

    profile = relationship('Profile', back_populates='foreign_login')


class ConfirmationCode(Base):
    __tablename__ = 'confirmation_codes'

    code = Column(String, primary_key=True)

    profile_id = Column(Integer, ForeignKey(Profile.id), unique=True)
    profile = relationship('Profile', backref='confirmation_code')

    date_created = Column(DateTime)

class Group(Base):
    __tablename__ = 'groups'

    id = Column(String(10), primary_key=True)

    coordinator_id = Column(Integer, ForeignKey('profiles.id'))
    coordinator = relationship('Profile', backref=backref('coordinated_groups', uselist=True,), foreign_keys=[coordinator_id])

    members = relationship('Profile', back_populates='group', foreign_keys=[Profile.group_id])

    group_requests = relationship('GroupJoinRequest', back_populates='group', cascade='all, delete')

    avatar_id = Column(VARCHAR(50), ForeignKey('group_avatars.id'), nullable=True)
    avatar = relationship('GroupAvatar', backref=backref('group', uselist=False), cascade='all, delete')

    name = Column(String(255))
    description = Column(String)
    graduation_year = Column(Integer)
    date_created = Column(Date)

    @hybrid_property
    def members_count(self):
        return len(self.members)

    @hybrid_property
    def reflections_count(self):
        sum = 0
        for member in self.members:
            sum += member.reflections_count
        return sum

    @hybrid_property
    def graduation_year_string(self):
        return str(self.graduation_year)

    @graduation_year_string.expression
    def graduation_year_string(cls):
        return type_coerce(cls.graduation_year, String)

    @hybrid_property
    def full_text(self):
        return self.name + ' ' + self.graduation_year_string
        # return self.name + ' ' + str(self.graduation_year)

#   This model will be used for profile pictures
class GroupAvatar(Base):
    __tablename__ = 'group_avatars'

    id = Column(VARCHAR(50), primary_key=True)

    saved_path = Column(String)
    filename = Column(String)
    date_added = Column(Date)

class GroupJoinRequest(Base):   
    __tablename__ = 'group_requests'

    group_id = Column(String(10), ForeignKey(Group.id), primary_key=True)
    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)
    
    group = relationship(Group, back_populates='group_requests')
    profile = relationship(Profile, back_populates='group_requests')

    date_added = Column(Date)
    #proposal = 

class NotificationRecipient(Base):
    __tablename__ = 'notifications_recipients_association'
    profile_id = Column(Integer, ForeignKey('profiles.id'), primary_key=True)
    notification_id = Column(Integer, ForeignKey('notifications.id'), primary_key=True)
    read = Column(Boolean, default=False)

    notification = relationship('Notification', back_populates='notification_recipients')
    recipient = relationship('Profile', back_populates='notifications')

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)

    profile_id = Column(Integer, ForeignKey(Profile.id))
    author = relationship('Profile', back_populates='notifications_authored')

    content = Column(String(200))
    date_sent = Column(DateTime)

    notification_recipients = relationship('NotificationRecipient', back_populates='notification', cascade='all, delete')


favourites = Table('favourites', Base.metadata,
    Column('reflection_id', Integer, ForeignKey('reflections.id')),
    Column('profile_id', Integer, ForeignKey('profiles.id')),
)

tags_reflections = Table('tags_reflections', Base.metadata, 
    Column('reflection_id', Integer, ForeignKey('reflections.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Attachment(Base):
    __tablename__ = 'attachments'

    id = Column(String , primary_key=True)

    reflection_id = Column(Integer, ForeignKey('reflections.id'))
    reflection = relationship('Reflection', back_populates='attachments')

    saved_path = Column(String(200))
    filename = Column(String(200))
    date_added = Column(DateTime, server_default=func.now())


class Reflection(Base):
    __tablename__ = 'reflections'

    id = Column(Integer, primary_key=True)

    profile_id = Column(Integer, ForeignKey(Profile.id))
    author = relationship('Profile', back_populates='reflections')

    title = Column(String(100))
    text_content = Column(Text)
    date_added = Column(DateTime)
    creativity = Column(Boolean)
    activity = Column(Boolean)
    service = Column(Boolean)

    post_visibility = Column(Integer, default=0)


    attachments = relationship('Attachment', back_populates='reflection', cascade='all, delete')

    comments = relationship('Comment', back_populates='reflection', cascade='all, delete')

    favouritees = relationship('Profile', secondary=favourites, back_populates='favourited')

    # reports = relationship('ReflectionReport', back_populates='reflection')

    tags = relationship('Tag', secondary=tags_reflections, back_populates='reflections')

    @hybrid_property
    def full_text(self):
        return self.title + self.text_content

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)

    name = Column(String(30))
    date_added = Column(Date)

    reflections = relationship('Reflection', secondary=tags_reflections, back_populates='tags')

class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True)

    profile_id = Column(Integer, ForeignKey(Profile.id))
    author = relationship('Profile', back_populates='comments')

    reflection_id = Column(Integer, ForeignKey(Reflection.id))
    reflection = relationship('Reflection', back_populates='comments')

    content = Column(String(200))
    date_added = Column(DateTime)

    # reports = relationship('CommentReport', back_populates='comment')


# class ReflectionReport(Base):
#     __tablename__ = 'reflection_reports'

#     id = Column(Integer, primary_key=True)

#     reflection_id = Column(Integer, ForeignKey('reflections.id'))
#     reflection = relationship('Reflection', back_populates='reports')

#     reason = Column(Text)
#     date_added = Column(Date)

# class CommentReport(Base):
#     __tablename__ = 'comment_reports'

#     id = Column(Integer, primary_key=True)

#     comment_id = Column(Integer, ForeignKey('comments.id'))
#     comment = relationship('Comment', back_populates='reports')

#     reason = Column(Text)
#     date_added = Column(Date)

# class Message(Base):
#     __tablename__ = 'messages'

#     id = Column(Integer, primary_key=True)

#     sender_id = Column(Integer, ForeignKey('profiles.id'))
#     sender = relationship(Profile, back_populates='sent_messages', foreign_keys=[sender_id])

#     receiver_id = Column(Integer, ForeignKey('profiles.id'))
#     receiver = relationship(Profile, back_populates='received_messages', foreign_keys=[receiver_id])

#     content = Column(Text(300))

#     datetime_sent = Column(DateTime, default=datetime.now())



@event.listens_for(Attachment, 'after_delete')
def receive_after_delete(mapper, connection, target):
    remove_file(getattr(target, 'saved_path'))

@event.listens_for(ProfileAvatar, 'after_delete')
def receive_after_delete(mapper, connection, target):
    remove_file(getattr(target, 'saved_path'))

@event.listens_for(GroupAvatar, 'after_delete')
def receive_after_delete(mapper, connection, target):
    remove_file(getattr(target, 'saved_path'))

