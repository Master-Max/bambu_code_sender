import os
import imaplib
import email
from email.header import decode_header

import requests
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_URL = os.getenv("EMAIL_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def decode_mime_header(value):
    if not value:
        return ""

    result = ""
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            result += part.decode(encoding or "utf-8", errors="replace")
        else:
            result += part

    return result


def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if (
                part.get_content_type() == "text/plain"
                and "attachment" not in str(part.get("Content-Disposition", ""))
            ):
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(errors="replace")

    return ""


def get_latest_unread_email():
    mail = imaplib.IMAP4_SSL(EMAIL_URL)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("INBOX")

    status, data = mail.search(None, "UNSEEN")

    if not data[0]:
        mail.logout()
        return None

    email_id = data[0].split()[-1]

    _, msg_data = mail.fetch(email_id, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])

    email_info = {
        "from": decode_mime_header(msg.get("From")),
        "subject": decode_mime_header(msg.get("Subject")),
        "body": get_email_body(msg).strip(),
    }

    mail.store(email_id, "+FLAGS", "\\Seen")
    mail.logout()

    return email_info


def send_to_discord(email_info):
    message = (
        f"📧 **New Email**\n\n"
        f"**From:** {email_info['from']}\n"
        f"**Subject:** {email_info['subject']}\n\n"
        f"```{email_info['body'][:1500]}```"
    )

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=10,
    )

    response.raise_for_status()

    print("Sent to Discord")


if __name__ == "__main__":
    email_info = get_latest_unread_email()

    if email_info:
        send_to_discord(email_info)
    else:
        print("No unread emails found")
