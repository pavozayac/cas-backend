from fastapi import HTTPException, status
from .models import Profile

#
#   This is here to avoid circular imports
#

def CREDENTIALS_EXCEPTION(detail = 'Invalid credentials'):
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail=detail
    )

def check_profile_id_ownership(object, profile: Profile):
    if object.profile_id != profile.id:
        raise CREDENTIALS_EXCEPTION('Invalid onwership')


