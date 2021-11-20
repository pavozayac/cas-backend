from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
from os import getenv

load_dotenv()

frontend_url = getenv('FRONTEND_CONFIRM_URL')

conf = ConnectionConfig(
    MAIL_USERNAME="casportal.testmail",
    MAIL_PASSWORD="jL7QHh36SnxFm2T",
    MAIL_FROM="casportal.testmail@casportal.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

confirmation_html = """
<p> Click here in order to confirm your email address. </p>
<a href="{}">Confirm email.</a>
"""


async def send_confirmation_mail(email: str, code: str):
    message = MessageSchema(
        subject='CasPortal Email Confirmation',
        recipients=[email],
        body=confirmation_html.format(f'{frontend_url+code}'),
        subtype='html'
    )

    fm = FastMail(conf)

    await fm.send_message(message)

recovery_html = """
<p> Click here in order to recover your password. </p>
<a href="{}">Recover password.</a>
"""

async def send_recovery_mail(email: str, code: str):
    message = MessageSchema(
        subject='CasPortal Password Recovery',
        recipients=[email],
        body=recovery_html.format(f'{frontend_url+code}'),
        subtype='html'
    )

    fm = FastMail(conf)

    await fm.send_message(message)
