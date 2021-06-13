from fastapi import HTTPException, status

#
#   This is here to avoid circular imports
#

def CREDENTIALS_EXCEPTION(detail = 'Invalid credentials'):
        return HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )

SECRET_KEY = '2f23ebdabb89ea8db60aad506cf762b274228190dbca6157622642b79bfb174b'
