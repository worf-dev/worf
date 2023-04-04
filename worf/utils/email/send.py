import traceback
import logging
import datetime
import smtplib

from worf.settings import settings
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import format_datetime

logger = logging.getLogger(__name__)


def send_email(to, subject, text=None, html=None, attachments=None, config=None):
    logger.debug("Sending an e-mail...")

    if config is None:
        config = settings.get("smtp")

    if text is None and html is None:
        raise ValueError("text or html (or both) needs to be defined!")

    sender_name = settings.get("name", "[No-Name]")

    msg = MIMEMultipart("mixed")
    msg["From"] = config["from"]
    msg["To"] = to
    msg["Subject"] = Header(subject, "utf-8")
    msg["Date"] = format_datetime(datetime.datetime.utcnow())

    msg_alternative = MIMEMultipart("alternative")

    if text:
        msg_alternative.attach(MIMEText(text, "plain", "utf-8"))
    if html:
        msg_alternative.attach(MIMEText(html, "html", "utf-8"))

    msg.attach(msg_alternative)

    if settings.get("test"):
        if hasattr(settings, "test_queue"):
            settings.test_queue.put({"type": "email", "data": msg})
        return msg

    if attachments is not None:
        # we assume that content is a byte-string
        for name, content in attachments.items():
            part = MIMEBase("application", "octet-stream")
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={name}")
            msg.attach(part)

    try:
        if config.get("ssl"):
            smtp = smtplib.SMTP_SSL(config["server"], config["port"])
        else:
            smtp = smtplib.SMTP(config["server"], config["port"])
        smtp.ehlo()
        if config.get("tls"):
            smtp.starttls()
        smtp.ehlo()
        smtp.login(config["username"], config["password"])
        smtp.sendmail(msg["From"], msg["To"], msg.as_string().encode("ascii"))
        smtp.quit()
        logger.debug("Successfully sent e-mail.")
    except:
        logger.error("Could not send e-mail:", traceback.format_exc())
