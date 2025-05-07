from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

SMTP_HOST = "localhost"
SMTP_PORT = 1025
SENDER_EMAIL = 'donot-reply@household.project'
SENDER_PASSWORD = ''

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(to, subject, content_body):
    try:
        msg = MIMEMultipart()
        msg["To"] = to
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg.attach(MIMEText(content_body, 'html'))
        
        logger.info(f"Connecting to SMTP server {SMTP_HOST}:{SMTP_PORT}")
        client = SMTP(host=SMTP_HOST, port=SMTP_PORT)
        client.send_message(msg=msg)
        client.quit()
        logger.info(f"Email sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")