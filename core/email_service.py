import smtplib
import logging

from email.message import EmailMessage
from core.config import settings

logger = logging.getLogger(__name__)


# =====================================================
# SIMPLE EMAIL FUNCTION
# =====================================================
def sendmail(to: str, subject: str, body: str) -> bool:
    try:
        msg = EmailMessage()
        msg["From"] = settings.MAIL_USERNAME
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {to}")
        return True

    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False


# =====================================================
# EMAIL SERVICE CLASS
# Old code support + new format
# =====================================================
class EmailService:

    # BASIC EMAIL
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> bool:
        try:
            msg = EmailMessage()
            msg["From"] = settings.MAIL_USERNAME
            msg["To"] = to_email
            msg["Subject"] = subject

            if html:
                msg.add_alternative(body, subtype="html")
            else:
                msg.set_content(body)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False

    # OTP EMAIL
    @staticmethod
    async def send_otp_email(to_email: str, otp: str) -> bool:
        body = f"""
Dear User,

Your OTP is: {otp}

This OTP is valid for 5 minutes.

Do not share this OTP with anyone.

Thanks,
LSP Team
"""
        return await EmailService.send_email(
            to_email=to_email,
            subject="Email Verification OTP",
            body=body
        )

    # EMAIL WITH ATTACHMENT
    @staticmethod
    async def send_email_with_attachment(
        to_email: str,
        subject: str,
        body: str,
        file_bytes: bytes,
        filename: str
    ) -> bool:
        try:
            msg = EmailMessage()
            msg["From"] = settings.MAIL_USERNAME
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(body)

            msg.add_attachment(
                file_bytes,
                maintype="application",
                subtype="octet-stream",
                filename=filename
            )

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.send_message(msg)

            logger.info(f"Attachment email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Attachment email failed: {e}")
            return False