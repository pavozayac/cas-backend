from datetime import date
from pydantic.errors import IntegerError
from sqlalchemy import Column, ForeignKey, String, Boolean, Date, Integer, Enum, DateTime, Table, Text
from sqlalchemy.orm import relation, relationship, backref
from sqlalchemy.sql.traversals import ColIdentityComparatorStrategy

from ..database import Base


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

    group_requests = relationship('GroupJoinRequest', back_populates='profile')

    notifications = relationship('Notification', secondary='notifications_recipients', back_populates='recipients')

    reflections = relationship('Reflection', back_populates='author')

    comments = relationship('Comment', back_populates='author')

    favourited = relationship('Reflection', secondary='favourites', back_populates='favouritees')

    basic_login = relationship('BasicLogin', back_populates='profile', cascade='all, delete')

class BasicLogin(Base):
    __tablename__ = 'basic_logins'

    profile_id = Column(Integer, ForeignKey(Profile.id), primary_key=True)

    email = Column(String(100), unique=True)
    password = Column(String)
    verification_sent = Column(Boolean)
    verified = Column(Boolean)

    profile = relationship('Profile', backref=backref('profiles', uselist=False), foreign_keys=[profile_id])

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

    group_requests = relationship('GroupJoinRequest', back_populates='group')

    name = Column(String)
    graduation_year = Column(Integer)
    date_created = Column(Date)


class GroupJoinRequest(Base):   
    __tablename__ = 'group_requests'

    id = Column(Integer, primary_key=True)

    group_id = Column(String(10), ForeignKey(Group.id))
    profile_id = Column(Integer, ForeignKey(Profile.id))
    
    group = relationship(Group, back_populates='group_requests')
    profile = relationship(Profile, back_populates='group_requests')

    date_added = Column(Date)
    #proposal = 

notifiactions_recipients = Table('notifications_recipients', Base.metadata,
    Column('profile_id', Integer, ForeignKey('profiles.id')),
    Column('notification_id', Integer, ForeignKey('notifications.id'))
)


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)

    content = Column(String(200))
    date_sent = Column(DateTime)

    recipients = relationship('Profile', secondary=notifiactions_recipients, back_populates='notifications')


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

    id = Column(Integer, primary_key=True)

    reflection_id = Column(Integer, ForeignKey('reflections.id'))
    reflection = relationship('Reflection', back_populates='attachments')

    saved_path = Column(String)
    filename = Column(String)
    date_added = Column(Date)


class Reflection(Base):
    __tablename__ = 'reflections'

    id = Column(Integer, primary_key=True)

    profile_id = Column(Integer, ForeignKey(Profile.id))
    author = relationship('Profile', back_populates='reflections')

    title = Column(String(100))
    text_content = Column(Text)
    slug = Column(String(255), unique=True)
    date_added = Column(DateTime)
    creativity = Column(Boolean)
    activity = Column(Boolean)
    service = Column(Boolean)

    attachments = relationship('Attachment', back_populates='reflection')

    comments = relationship('Comment', back_populates='reflection', cascade='all, delete')

    favouritees = relationship('Profile', secondary=favourites, back_populates='favourited')

    reports = relationship('ReflectionReport', back_populates='reflection')

    tags = relationship('Tag', secondary=tags_reflections, back_populates='reflections')

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)

    name = Column(String(50))
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

    reports = relationship('CommentReport', back_populates='comment')


class ReflectionReport(Base):
    __tablename__ = 'reflection_reports'

    id = Column(Integer, primary_key=True)

    reflection_id = Column(Integer, ForeignKey('reflections.id'))
    reflection = relationship('Reflection', back_populates='reports')

    reason = Column(Text)
    date_added = Column(Date)

class CommentReport(Base):
    __tablename__ = 'comment_reports'

    id = Column(Integer, primary_key=True)

    comment_id = Column(Integer, ForeignKey('comments.id'))
    comment = relationship('Comment', back_populates='reports')

    reason = Column(Text)
    date_added = Column(Date)

