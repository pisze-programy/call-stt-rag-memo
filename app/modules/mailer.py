import os
import smtplib
import logging
from email.message import EmailMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Mailer:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 465
        self.sender_email = os.getenv("EMAIL_USER")
        self.app_password = os.getenv("EMAIL_PASS")
        self.sender_name = "Notia Assistant"

        if not self.sender_email or not self.app_password:
            raise EnvironmentError("Missing EMAIL_USER or EMAIL_PASS environment variables")

    def send(self, to_email: str, subject: str, body: str) -> bool:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        msg['To'] = to_email
        msg.set_content(body)

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)
            logger.info(f"Email successfully sent to {to_email}")
            return True
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False