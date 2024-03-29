from secrets import token_urlsafe
from sqlalchemy.exc import IntegrityError
import time
import sqlalchemy
from sqlalchemy.orm import Session, query
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.relationships import foreign
from sqlalchemy.sql.schema import UniqueConstraint
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from . import schemas, models
from .. import settings
from ..utils import filter_from_schema, filter_visibility, paginate, sort_from_schema, save_generic_attachment, delete_generic_attachment
from datetime import date, datetime, timedelta
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
        date_joined=date.today(),
        last_online=date.today()
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
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            'Could not find profile with this id')

    return profile


def read_profile_by_email(db: Session, email: str):
    login = db.query(models.BasicLogin).filter(
        models.BasicLogin.email == email).first()

    if login is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Profile not found')

    return login.profile


def read_profile_by_foreign_id(db: Session, id: int):
    login = db.query(models.ForeignLogin).filter(
        models.ForeignLogin.foreign_id == id).first()

    if login is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Profile not found')

    return db.query(models.Profile).filter(models.Profile.id == login.profile_id).one()


def read_profile_by_foreign_email(db: Session, email: str):
    login = db.query(models.ForeignLogin).filter(
        models.ForeignLogin.email == email).first()

    if login is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Profile not found')

    return login.profile


def filter_profiles(db: Session, pagination: schemas.Pagination, filters: schemas.ProfileFilters, sorts: schemas.ProfileSorts):
    search = db.query(models.Profile)
    search = filter_from_schema(search, filters)
    search = sort_from_schema(search, sorts)
    count = search.count()
    search = paginate(search, pagination)

    return search.all(), count


def update_profile(db: Session, instance: models.Profile, schema: schemas.ProfileIn):
    if instance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Profile with this ID not found.')

    instance.first_name = schema.first_name
    instance.last_name = schema.last_name

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
        raise HTTPException(status.HTTP_409_CONFLICT,
                            'This email address is already in use.')

    basic_obj = models.BasicLogin(
        profile_id=profile_id,
        email=basic_login.email,
        password=password_context.hash(basic_login.password),
        verification_sent=False,
        verified=False
    )

    db.add(basic_obj)
    db.commit()
    db.refresh(basic_obj)
    return basic_obj


def read_basic_login_by_email(db: Session, email: str):
    return db.query(models.BasicLogin).filter(models.BasicLogin.email == email).first()


def read_basic_login_by_profile(db: Session, profile_id: int):
    return db.query(models.BasicLogin).filter(models.BasicLogin.profile_id == profile_id).one()


def update_basic_login(db: Session, basic_login: models.BasicLogin, basic_login_in: schemas.BasicLoginIn):
    basic_login.password = password_context.hash(basic_login_in.password)

    db.commit()
    db.refresh(basic_login)
    return basic_login


#
#   ForeignLogin CRUD
#


def create_foreign_login(db: Session, email: str, profile_id: int, foreign_id: str, provider: str):
    foreign_login = models.ForeignLogin(
        profile_id=profile_id,
        foreign_id=foreign_id,
        email=email,
        provider=provider
    )

    db.add(foreign_login)
    db.commit()
    db.refresh(foreign_login)
    return foreign_login


def read_foreign_login(db: Session, foreign_id: str):
    foreign_login = db.query(models.ForeignLogin).filter(
        models.ForeignLogin.foreign_id == foreign_id).first()

    if foreign_login is None:
        raise HTTPException(HTTP_404_NOT_FOUND,
                            'Foreign login with this id was not found')

    return foreign_login


#
#   Confirmation/recovery hybrid code CRUD
#


def create_confirmation_code(db: Session, code: str, profile_id: int):
    confirmation_code = models.ConfirmationCode(
        profile_id=profile_id,
        code=code,
        date_created=datetime.now()
    )
    try:
        check_code = db.query(models.ConfirmationCode).filter(
            models.ConfirmationCode.profile_id == profile_id).one()
        if check_code.date_created < datetime.now()-timedelta(minutes=15):
            db.delete(check_code)
            db.commit()
        else:
            raise HTTPException(
                HTTP_409_CONFLICT, 'Recovery email has already been sent, try again in 15 minutes')
    except NoResultFound:
        pass

    try:
        db.add(confirmation_code)
        db.commit()
        db.refresh(confirmation_code)
    except IntegrityError:
        raise HTTPException(HTTP_409_CONFLICT,
                            'Recovery email has already been sent.')
    return confirmation_code


def read_confirmation_code(db: Session, code: str) -> models.ConfirmationCode:
    try:
        confirmation_code = db.query(models.ConfirmationCode).filter(
            models.ConfirmationCode.code.like(code)).one()
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Confirmation code is invalid')

    return confirmation_code


def delete_confirmation_code(db: Session, confirmation_code: models.ConfirmationCode):
    db.delete(confirmation_code)
    db.commit()

#
#   Group CRUD
#


def create_group(db: Session, group: schemas.GroupIn, coordinator_id: int):
    coordinator = db.query(models.Profile).filter(
        models.Profile.id == coordinator_id).one()

    new_group = models.Group(
        id=token_urlsafe(6),
        coordinator_id=coordinator_id,
        **group.dict(),
        date_created=date.today()
    )

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    db.commit()

    return new_group


def read_group_by_id(db: Session, id: str):
    return db.query(models.Group).filter(models.Group.id == id).one()


def filter_groups(db: Session, pagination: schemas.Pagination, filters: schemas.GroupFilters, sorts: schemas.GroupSorts):
    groups = db.query(models.Group)
    groups = filter_from_schema(groups, filters)
    groups = sort_from_schema(groups, sorts)
    count = groups.distinct().count()
    groups = paginate(groups, pagination)

    return groups.all(), count


def update_group(db: Session, instance: models.Group, group: schemas.GroupIn):
    # instance.coordinator_id = group.coordinator_id
    instance.name = group.name
    instance.graduation_year = group.graduation_year
    instance.description = group.description

    db.commit()
    db.refresh(instance)
    return instance


def delete_group(db: Session, instance: models.Group):
    db.delete(instance)
    db.commit()


#
#   Group Avatar CRUD
#

async def create_group_avatar(db: Session, avatar: schemas.AvatarIn, group: models.Profile, file: UploadFile):
    if group.avatar is not None:
        raise HTTPException(HTTP_400_BAD_REQUEST,
                            'Avatar already present, use PUT')

    generated_path, id = await save_generic_attachment(file)

    avatar_obj = models.GroupAvatar(
        id=str(id),
        filename=avatar.filename,
        saved_path=generated_path,
        date_added=date.today()
    )

    group.avatar = avatar_obj

    db.add(avatar_obj)
    db.commit()
    db.refresh(avatar_obj)
    return avatar_obj


def read_group_avatar(db: Session, id: str):
    avatar = db.query(models.GroupAvatar).filter(
        models.GroupAvatar.id == id).first()

    if avatar is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Avatar not found')

    return avatar


async def update_group_avatar(db: Session, avatar: schemas.AvatarIn, group: models.Group, file: UploadFile):

    if group is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Group not found')

    generated_path, attachment_id = await save_generic_attachment(file)

    if group.avatar:
        if not os.path.exists(group.avatar.saved_path):
            raise HTTPException(status.HTTP_409_CONFLICT,
                                'The attachment is not available.')

    avatar_obj = models.GroupAvatar(
        id=str(attachment_id),
        filename=avatar.filename,
        saved_path=generated_path,
        date_added=date.today()
    )

    if group.avatar:
        db.delete(group.avatar)

    group.avatar = avatar_obj

    print('bruh')

    db.commit()
    db.refresh(avatar_obj)

    return avatar_obj


def delete_group_avatar(db: Session, group: models.Profile):
    if group.avatar is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            'Profile does not have avatar')

    if not os.path.exists(group.avatar.saved_path):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            'The attachment is not available.')

    db.delete(group.avatar)
    db.commit()


#
#   GroupJoinRequests CRUD
#

def create_group_join_request(db: Session, profile_id: int, group_id: int):
    group_join_obj = models.GroupJoinRequest(
        group_id=group_id,
        profile_id=profile_id,
        date_added=date.today()
    )

    try:
        db.add(group_join_obj)
        db.commit()
    except IntegrityError:
        raise HTTPException(HTTP_409_CONFLICT, 'Join request already posted')
    db.refresh(group_join_obj)
    return group_join_obj


def read_group_join_request_by_ids(db: Session, group_id: int, profile_id: int):
    return db.query(models.GroupJoinRequest).filter(models.GroupJoinRequest.group_id == group_id and models.GroupJoinRequest.profile_id == profile_id).first()


def read_group_join_requests_by_group(db: Session, group_id: int):
    return db.query(models.GroupJoinRequest).filter(models.GroupJoinRequest.group_id == group_id).all()


def delete_group_join_request(db: Session, instance: models.GroupJoinRequest):
    db.delete(instance)
    db.commit()

#
#   Notifications CRUD
#


def create_notification(db: Session, notification: schemas.NotificationIn, profile: models.Profile):
    notification_obj = models.Notification(
        profile_id=profile.id,
        content=notification.content,
        date_sent=datetime.now()
    )

    for id in notification.recipients:
        recipient = db.query(models.Profile).filter(
            models.Profile.id == id).one_or_none()

        if recipient is not None:
            association = models.NotificationRecipient()
            db.add(association)
            association.recipient = recipient

            notification_obj.notification_recipients.append(association)

        else:
            raise HTTPException(HTTP_404_NOT_FOUND,
                                f'Recipient with id {id} not found')

    db.add(notification_obj)
    db.commit()
    db.refresh(notification_obj)
    return notification_obj


def filter_notifications_by_recipient(db: Session, sorts: schemas.NotificationSorts, filters: schemas.NotificationFilters, pagination: schemas.Pagination,  profile: models.Profile):
    notes = db.query(models.Notification)
    notes = sort_from_schema(notes, sorts)

    if filters.dict().get('read') is not None:
        notes = notes.filter(
            models.Notification.notification_recipients.any((models.NotificationRecipient.recipient == profile) & (models.NotificationRecipient.read == filters.read))).distinct()
    else:
        notes = notes.filter(
            models.Notification.notification_recipients.any(models.NotificationRecipient.recipient == profile)).distinct()

    if sorts.dict().get('read_omit') is not None:
        if sorts.read_omit == 'asc':
            notes = notes.join(models.NotificationRecipient, sqlalchemy.and_(models.NotificationRecipient.profile_id == profile.id,
                               models.NotificationRecipient.notification_id == models.Notification.id)).order_by(sqlalchemy.asc(models.NotificationRecipient.read))
        else:
            notes = notes.join(models.NotificationRecipient, sqlalchemy.and_(models.NotificationRecipient.profile_id == profile.id,
                    models.NotificationRecipient.notification_id == models.Notification.id)).order_by(sqlalchemy.desc(models.NotificationRecipient.read))

    count = notes.count()
    read_count = db.query(models.NotificationRecipient).filter(
        (models.NotificationRecipient.profile_id == profile.id) & (models.NotificationRecipient.read == True)).count()
    notes = paginate(notes, pagination)

    return notes.distinct().all(), count, read_count


def filter_authored_notifications(db: Session, sorts: schemas.NotificationSorts, pagination: schemas.Pagination,  profile: models.Profile):
    notes = db.query(models.Notification).filter(
        models.Notification.author == profile)
    notes = sort_from_schema(notes, sorts)
    count = notes.count()
    read_count = db.query(models.NotificationRecipient).filter((models.NotificationRecipient.notification.has(
        models.Notification.profile_id == profile.id)) & (models.NotificationRecipient.read == True)).count()
    notes = paginate(notes, pagination)

    return notes.all(), count, read_count


def read_notification_by_id(db: Session, id: int, profile: models.Profile):
    notification = db.query(models.Notification).filter(
        models.Notification.id == id).one_or_none()

    if notification is None:
        raise HTTPException(HTTP_404_NOT_FOUND,
                            'Notification with this id was not found')

    note_recipient = db.query(models.NotificationRecipient).filter(
        (models.NotificationRecipient.notification_id == notification.id) & (models.NotificationRecipient.profile_id == profile.id)).one_or_none()

    if note_recipient is None and profile.is_admin == False:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            'Insufficient permissions')

    notification.read = note_recipient.read

    return notification


def read_notification_by_id_no_read(db: Session, id: int, profile: models.Profile):
    notification = db.query(models.Notification).filter(
        models.Notification.id == id).one_or_none()

    if notification is None:
        raise HTTPException(HTTP_404_NOT_FOUND,
                            'Notification with this id was not found')

    note_recipient = db.query(models.NotificationRecipient).filter(
        (models.NotificationRecipient.notification_id == notification.id) & (models.NotificationRecipient.profile_id == profile.id)).one_or_none()

    if note_recipient is None and profile.is_admin == False:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            'Insufficient permissions')

    return notification


def update_notification(db: Session, instance: models.Notification, notfification: schemas.NotificationIn):
    instance.content = notfification.content

    new_recipients = []
    for recipient_id in notfification.recipients:
        recip = db.query(models.Profile).filter(
            models.Profile.id == recipient_id).first()

        if recip is not None:
            new_recipients.append(recip)

    instance.recipients = new_recipients

    db.commit()
    db.refresh(instance)
    return instance


def delete_notification(db: Session, instance: models.Notification):
    db.delete(instance)
    db.commit()


def toggle_read_notification(db: Session, profile: models.Profile, notification: models.Notification):
    try:
        notification_recipient = db.query(models.NotificationRecipient).filter(
            (models.NotificationRecipient.notification_id == notification.id) & (models.NotificationRecipient.profile_id == profile.id)).one()
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Notification not found')

    notification_recipient.read = not notification_recipient.read

    db.commit()


#
#   Profile Avatar CRUD
#


async def create_profile_avatar(db: Session, avatar: schemas.AvatarIn, profile: models.Profile, file: UploadFile):
    if profile.avatar is not None:
        raise HTTPException(HTTP_400_BAD_REQUEST,
                            'Avatar already present, use PUT')

    generated_path, id = await save_generic_attachment(file)

    avatar_obj = models.ProfileAvatar(
        id=str(id),
        filename=avatar.filename,
        saved_path=generated_path,
        date_added=date.today()
    )

    profile.avatar = avatar_obj

    db.add(avatar_obj)
    db.commit()
    db.refresh(avatar_obj)
    return avatar_obj


def read_profile_avatar(db: Session, avatar_id: str):
    print(id)
    try:
        profile_avatar = db.query(models.ProfileAvatar).filter(
            models.ProfileAvatar.id == avatar_id).one()
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Avatar not found')

    return profile_avatar


async def update_profile_avatar(db: Session, avatar: schemas.AvatarIn, profile: models.Profile, file: UploadFile):
    generated_path, id = await save_generic_attachment(file)

    if profile.avatar and os.path.exists(profile.avatar.saved_path):
        db.delete(profile.avatar)

    avatar_obj = models.ProfileAvatar(
        id=str(id),
        filename=avatar.filename,
        saved_path=generated_path,
        date_added=date.today()
    )

    if profile.avatar:
        db.delete(profile.avatar)
    profile.avatar = avatar_obj
    db.commit()
    db.refresh(avatar_obj)

    return avatar_obj


def delete_profile_avatar(db: Session, profile: models.Profile):
    if profile.avatar is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            'Profile does not have avatar')

    if not os.path.exists(profile.avatar.saved_path):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            'The attachment is not available.')

    db.delete(profile.avatar)
    db.commit()

#
#   Reflections CRUD
#


def create_reflection(db: Session, profile_id: int, reflection: schemas.ReflectionIn):
    tags_list = []

    for tag in reflection.tags:
        if read_tag_by_name(db, tag.name) is None:
            create_tag(db, tag)

        retrieved_tag = read_tag_by_name(db, tag.name)
        tags_list.append(retrieved_tag)

    reflection_obj = models.Reflection(
        profile_id=profile_id,
        title=reflection.title,
        text_content=reflection.text_content,
        date_added=datetime.now(),
        post_visibility=reflection.post_visibility,
        creativity=reflection.creativity,
        activity=reflection.activity,
        service=reflection.service,
        tags=tags_list
    )

    profile = read_profile_by_id(db, profile_id)

    db.add(reflection_obj)
    db.commit()
    db.refresh(reflection_obj)

    reflection_obj.is_favourite = True if profile in reflection_obj.favouritees else False

    return reflection_obj

# The profile is required for annotating the model with information whether a reflection is favourited


def read_reflection_by_id(db: Session, id: int, profile: models.Profile):
    reflection = db.query(models.Reflection).filter(
        models.Reflection.id == id).first()

    if reflection is None:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Reflection not found')

    reflection.is_favourite = True if profile in reflection.favouritees else False

    return reflection


def filter_reflections(db: Session, pagination: schemas.Pagination, filters: schemas.ReflectionFilters, sorts: schemas.ReflectionSorts, profile: models.Profile):
    query = db.query(models.Reflection)
    query = filter_from_schema(query, filters)
    query = sort_from_schema(query, sorts)
    query = filter_visibility(query, profile)
    count = query.count()
    query = paginate(query, pagination)
    reflections = query.all()

    for ref in reflections:
        ref.is_favourite = True if profile in ref.favouritees else False
    return (reflections, count)


def filter_favourite_reflections(db: Session, pagination: schemas.Pagination, filters: schemas.ReflectionFilters, sorts: schemas.ReflectionSorts, profile: models.Profile):
    query = db.query(models.Reflection)
    query = filter_from_schema(query, filters)
    query = sort_from_schema(query, sorts)
    query = filter_visibility(query, profile)

    query = query.filter(models.Reflection.favouritees.any(
        models.Profile.id == profile.id))
    count = query.count()

    query = paginate(query, pagination)
    reflections = query.all()

    # favouriteReflections = []
    # for ref in reflections:
    #     ref.is_favourite = True if profile in ref.favouritees else False
    #     if ref.is_favourite == True:
    #         favouriteReflections.append(ref)

    return (reflections, count)


def update_reflection(db: Session, instance: models.Reflection, reflection: schemas.ReflectionIn):
    instance.title = reflection.title
    instance.text_content = reflection.text_content
    instance.post_visibility = reflection.post_visibility
    instance.creativity = reflection.creativity
    instance.activity = reflection.activity
    instance.service = reflection.service

    tags_list = []

    for tag in reflection.tags:
        if read_tag_by_name(db, tag.name) is None:
            create_tag(db, tag)

        retrieved_tag = read_tag_by_name(db, tag.name)
        tags_list.append(retrieved_tag)

    instance.tags = tags_list

    db.commit()
    db.refresh(instance)
    return instance


def delete_reflection(db: Session, instance: models.Reflection):
    db.delete(instance)
    db.commit()

#
#   Reflection Attachment CRUD
#


async def create_reflection_attachment(db: Session, attachment: schemas.AttachmentIn, file: UploadFile):
    generated_path, gen_id = await save_generic_attachment(file)

    attachment_obj = models.Attachment(
        id=str(gen_id),
        filename=attachment.filename,
        saved_path=str(generated_path),
        reflection_id=int(attachment.reflection_id),
        date_added=datetime.now()
    )

    db.add(attachment_obj)
    db.commit()
    db.refresh(attachment_obj)
    return attachment_obj


def read_reflection_attachment(db: Session, id: str):
    try:
        attachment = db.query(models.Attachment).filter(
            models.Attachment.id == id).one()
    except NoResultFound:
        raise HTTPException(HTTP_404_NOT_FOUND, 'Attachment not found')

    return attachment

    # if os.path.isfile(attachment.saved_path):
    #     return attachment
    # else:
    #     raise HTTPException(status.HTTP_410_GONE, 'The attachment is not available')


def delete_reflection_attachment(db: Session, attachment: models.Attachment):
    db.delete(attachment)
    db.commit()

#
#   Favourites CRUD
#


def create_favourite(db: Session, reflection: models.Reflection, profile: models.Profile):
    if profile not in reflection.favouritees:
        reflection.favouritees.append(profile)
    else:
        raise HTTPException(HTTP_409_CONFLICT, 'Already favourited')

    db.commit()


def delete_favourite(db: Session, reflection: models.Reflection, profile: models.Profile):
    if profile in reflection.favouritees:
        reflection.favouritees.remove(profile)
    else:
        raise HTTPException(HTTP_400_BAD_REQUEST,
                            'Cannot delete a favourite which does not exist')

    db.commit()

#
#   Tags CRUD
#


def create_tag(db: Session, tag: schemas.TagIn):
    tag_obj = models.Tag(
        name=tag.name,
        date_added=date.today()
    )

    db.add(tag_obj)
    db.commit()
    db.refresh(tag_obj)
    return tag_obj


def read_tags(db: Session):
    return db.query(models.Tag).all()


def read_tag_by_name(db: Session, name: str):
    retrieved = db.query(models.Tag).filter(
        models.Tag.name == name).one_or_none()

    return retrieved


def delete_tag(db: Session, instance: models.Tag):
    db.delete(instance)
    db.commit()

#
#   Comments CRUD
#


def create_comment(db: Session, profile_id: int, reflection_id: int, comment: schemas.CommentIn):
    comment_obj = models.Comment(
        profile_id=profile_id,
        reflection_id=reflection_id,
        content=comment.content,
        date_added=datetime.now()
    )

    db.add(comment_obj)
    db.commit()
    db.refresh(comment_obj)
    return comment_obj


def read_comment_by_id(db: Session, id: int):
    comment = db.query(models.Comment).filter(models.Comment.id == id).one()

    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Comment not found')

    return comment


def read_comments_by_reflection_id(db: Session, reflection_id: int):
    comments = db.query(models.Comment).filter(
        models.Comment.reflection_id == reflection_id).all()

    if comments is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'Comments not found')

    return comments


def filter_reflection_comments(db: Session, reflection_id: int, pagination: schemas.Pagination, sorts: schemas.CommentSorts):
    query = db.query(models.Comment).filter(
        models.Comment.reflection_id == reflection_id)
    query = sort_from_schema(query, sorts)
    count = query.count()
    query = paginate(query, pagination)

    comments = query.all()

    return comments, count


def update_comment(db: Session, instance: models.Comment, comment: schemas.CommentIn):
    instance.content = comment.content

    db.commit()
    db.refresh(instance)
    return instance


def delete_comment(db: Session, instance):
    db.delete(instance)
    db.commit()