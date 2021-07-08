import re
from pydantic.networks import HttpUrl
from pydantic.schema import schema
from sqlalchemy.orm import Session, query
from starlette.status import HTTP_404_NOT_FOUND
from . import schemas, models
from .. import settings
from ..utils import filter_from_schema, sort_from_schema
from datetime import date, datetime
from passlib.context import CryptContext
from fastapi import status, HTTPException, UploadFile
import aiofiles
import os
#
#   Profile CRUD
#   

def create_profile(db: Session, profile: schemas.ProfileIn):
    profile_obj = models.Profile(
        **profile.dict(),
        date_joined = date.today(),
        last_online = date.today()
    )

    db.add(profile_obj)
    db.commit()
    db.refresh(profile_obj)
    return profile_obj

def read_profiles(db: Session):
    return db.query(models.Profile).all()

def read_profile_by_id(db: Session, id: int):
    profile = db.query(models.Profile).filter(models.Profile.id == id).first()

    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Could not find profile with this id')
    
    return profile

def read_profile_by_email(db: Session, email: str):
    login = db.query(models.BasicLogin).filter(models.BasicLogin.email == email).first()
    return login.profile

def filter_profiles(db: Session, filters: schemas.ProfileFilters, sorts: schemas.ProfileSorts):
    search = db.query(models.Profile)
    search = filter_from_schema(search, models.Profile, filters)
    search = sort_from_schema(search, models.Profile, sorts)

    return search.all()

    

def update_profile(db: Session, instance: models.Profile, schema: schemas.ProfileIn):
    if instance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Profile with this ID not found.')

    instance.first_name = schema.first_name
    instance.last_name = schema.last_name
    instance.post_visibility = schema.post_visibility

    db.commit()
    db.refresh(instance)
    return instance

def delete_profile(db: Session, instance: models.Profile):
    db.delete(instance)
    db.commit()
    

#
#   BasicLogin CRUD
#

password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def create_basic_login(db: Session, profile_id: int, basic_login: schemas.BasicLoginIn):
    if read_basic_login_by_email(db, basic_login.email) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, 'This email address is already in use.')

    basic_obj = models.BasicLogin(
        profile_id = profile_id,
        email = basic_login.email,
        password = password_context.hash(basic_login.password),
        verification_sent = False,
        verified = False
    )

    db.add(basic_obj)
    db.commit()
    db.refresh(basic_obj)
    return basic_obj

def read_basic_login_by_email(db: Session, email: str):
    return db.query(models.BasicLogin).filter(models.BasicLogin.email == email).first()

#
#   ForeignLogin CRUD !!! TODO
#

#
#   Group CRUD
#

def create_group(db: Session, group: schemas.GroupIn, coordinator_id: int):
    new_group = models.Group(
        coordinator_id = coordinator_id,
        name = group.name,
        graduation_year = group.graduation_year,
        date_created = date.today()
    )

    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

def read_group_by_id(db: Session, id: int):
    return db.query(models.Group).filter(models.Group.id == id).first()

def filter_groups(db: Session, name = None, gyear_lte = None, gyear_gte = None):
    groups = db.query(models.Group)

    if name is not None:
        groups = groups.filter(models.Group.name.like(name))
    
    if gyear_lte is not None:
        groups = groups.filter(models.Group.graduation_year >= gyear_lte)

    if gyear_gte is not None:
        groups = groups.filter(models.Group.graduation_year <= gyear_gte)

    return groups.all()

def update_group(db: Session, instance: models.Group, group: schemas.GroupIn):
    instance.coordinator_id = group.coordinator_id
    instance.name = group.name
    instance.graduation_year = group.graduation_year

    db.commit()
    db.refresh(instance)
    return instance

def delete_group(db: Session, instance: models.Group):
    db.delete(instance)
    db.commit()

#   
#   GroupJoinRequests CRUD
#

def create_group_join_request(db: Session, profile_id: int, group_join: schemas.GroupJoinRequestIn):
    group_join_obj = models.GroupJoinRequest(
        group_id = group_join.group_id,
        profile_id = profile_id,
        date_added = date.today()
    )

    db.add(group_join_obj)
    db.commit()
    db.refresh(group_join_obj)
    return group_join_obj

def read_group_join_request_by_id(db: Session, id: int):
    return db.query(models.GroupJoinRequest).filter(models.GroupJoinRequest.id == id).first()

def read_group_join_requests_by_group(db: Session, group_id: int):
    return db.query(models.GroupJoinRequest).filter(models.GroupJoinRequest.group_id == group_id).all()

def delete_group_join_request(db: Session, instance: models.GroupJoinRequest):
    db.delete(instance)
    db.commit()

#
#   Notifications CRUD
#

def create_notification(db: Session, notification: schemas.NotificationIn):
    notification_obj = models.Notification(
        content = notification.content,
        date_sent = datetime.now()
    )

    for id in notification.recipients:
        recipient = db.query(models.Profile).filter(models.Profile.id == id).first()

        if recipient is not None:
            notification_obj.recipients.append(recipient)

    db.add(notification_obj)
    db.commit()
    db.refresh(notification_obj)
    return notification_obj

def read_notifications_by_recipient(db: Session, profile_id: int):
    notifications = db.query(models.Notification).filter(models.Notification.recipients.contains(profile_id)).all()
    
    return notifications

def update_notification(db: Session, instance: models.Notification, notfification: schemas.NotificationIn):
    instance.content = notfification.content
    
    new_recipients = []
    for recipient_id in notfification.recipients:
        recip = db.query(models.Profile).filter(models.Profile.id == recipient_id).first()

        if recip is not None:
            new_recipients.append(recip)

    instance.recipients = new_recipients

    db.commit()
    db.refresh(instance)
    return instance

def delete_notification(db: Session, instance: models.Notification):    
    db.delete(instance)
    db.commit()

#
#   Attachment CRUD
#

async def create_attachment(db: Session, attachment: schemas.AttachmentIn, file: UploadFile):
    generated_path = settings.ATTACHMENT_PATH + (split := file.filename.split('.')[0]) + str(datetime.now()) + split[1]

    with aiofiles.open(generated_path, 'wb') as aio_file:
        content = await file.read()
        await aio_file.write(content)


    attachment_obj = models.Attachment(
        reflection_id = attachment.reflection_id,
        filename = attachment.filename,
        saved_path = generated_path,
        date_added = date.today()
    )

    db.add(attachment_obj)
    db.commit()
    db.refresh(attachment_obj)
    return attachment_obj

def delete_attachment(db: Session, id: int):
    attachment = db.query(models.Attachment).filter(models.Attachment.id == id).first()

    if attachment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Attachment was not found')

    if not os.path.exists(attachment.saved_path):
        raise HTTPException(status.HTTP_409_CONFLICT, 'The attachment is not available.')

    os.remove(attachment.saved_path)

#
#   Reflections CRUD
#

def create_reflection(db: Session, profile_id: int, reflection: schemas.ReflectionIn):
    reflection_obj = models.Reflection(
        profile_id = profile_id,
        title = reflection.title,
        text_content = reflection.text_content,
        slug = reflection.title + str(datetime.now()),
        date_added = datetime.now(),
        creativity = reflection.creativity,
        activity = reflection.activity,
        service = reflection.service
    )

    db.add(reflection_obj)
    db.commit()
    db.refresh(reflection_obj)
    return reflection_obj

def read_reflection(db: Session, slug: str = None, id: int = None):
    if slug is not None:
        reflection = db.query(models.Reflection).filter(models.Reflection.slug == slug).first()
    if id is not None:
        reflection = db.query(models.Reflection).filter(models.Reflection.id == id).first()

    if reflection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Reflection with this slug does not exist')

    return reflection

def update_reflection(db: Session, instance: models.Reflection, reflection: schemas.ReflectionIn):
    instance.title = reflection.title
    instance.text_content = reflection.text_content
    instance.creativity = reflection.creativity
    instance.activity = reflection.activity
    instance.service = reflection.service

    db.commit()
    db.refresh(instance)
    return instance

def delete_reflection(db: Session, instance: models.Reflection):
    db.delete(instance)
    db.commit()

#
#   Tags CRUD
#   

def create_tag(db: Session, tag: schemas.TagIn):
    tag_obj = models.Tag(
        name = tag.name,
        date_added = date.today()
    )

    db.add(tag_obj)
    db.commit()
    db.refresh(tag_obj)
    return tag_obj

def read_tag_by_name(db: Session, name: str):
    retrieved = db.query(models.Tag).filter(models.Tag.name == name).first()

    if retrieved is None:
        raise HTTPException(404, 'Tag with this name was not found')

    return retrieved

def delete_tag(db: Session, instance: models.Tag):
    db.delete(instance)
    db.commit()

#
#   Comments CRUD
#

def create_comment(db: Session, profile_id: int, reflection_id: int, comment: schemas.CommentIn):
    comment_obj = models.Comment(
        profile_id = profile_id,
        reflection_id = reflection_id,
        content = comment.content,
        date_added = datetime.now()
    )

    db.add(comment_obj)
    db.commit()
    db.refresh(comment_obj)
    return comment_obj

def read_comment_by_id(db: Session, id: int):
    comment = db.query(models.Comment).filter(models.Comment.id == id).first()

    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Comment not found')

    return comment

def read_comments_by_reflection_id(db: Session, reflection_id: int):
    comments = db.query(models.Comment).filter(models.Comment.reflection_id == reflection_id).all()

    if comments is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Comments not found')
    
    return comments

def update_comment(db: Session, instance: models.Comment, comment: schemas.CommentIn):
    instance.content = comment.content

    db.commit()
    db.refresh(instance)
    return instance

def delete_comment(db: Session, instance):
    db.delete(instance)
    db.commit()

#
#   ReflectionReport CRUD
#

def create_reflection_report(db: Session, reflection_id: int, report: schemas.ReflectionReportIn):
    report_obj = models.ReflectionReport(
        reflection_id = reflection_id,
        reason = report.reason
    )

    db.add(report_obj)
    db.commit()
    db.refresh(report_obj)
    return report_obj

def read_reflection_report_by_id(db: Session, id: int):
    report = db.query(models.ReflectionReport).filter(models.ReflectionReport.id == id).first()

    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Reflection report not found')

    return report

def read_reports_by_reflection_id(db: Session, reflection_id: int):
    reports = db.query(models.ReflectionReport).filter(models.ReflectionReport.reflection_id == reflection_id).all()

    if reports is None: 
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Reflection reports not found')

    return reports

def delete_reflection_report(db: Session, id: int):
    report = db.query(models.ReflectionReport).filter(models.ReflectionReport.id == id).first()

    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Reflection report not found')

    db.delete(report)
    db.commit()

#
#   CommentReport CRUD
#

def create_comment_report(db: Session, comment_id: int, report: schemas.CommentReportIn):
    report_obj = models.CommentReport(
        reflection_id = comment_id,
        reason = report.reason
    )

    db.add(report_obj)
    db.commit()
    db.refresh(report_obj)
    return report_obj

def read_comment_report_by_id(db: Session, id: int):
    report = db.query(models.CommentReport).filter(models.CommentReport.id == id).first()

    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Reflection report not found')

    return report

def read_reports_by_comment_id(db: Session, comment_id: int):
    reports = db.query(models.CommentReport).filter(models.CommentReport.comment_id == comment_id).all()

    if reports is None: 
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Reflection reports not found')

    return reports

def delete_comment_report(db: Session, id: int):
    report = db.query(models.CommentReport).filter(models.CommentReport.id == id).first()

    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Reflection report not found')

    db.delete(report)
    db.commit()