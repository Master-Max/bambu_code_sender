import os
import re
import imaplib
import email
import requests
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_URL = os.getenv("EMAIL_URL", "imap.gmail.com")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

TARGET_SUBJECT = "Your Bambu Lab verification code"


def decode_header_value(value):
    if not value:
        return ""

    decoded = ""
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            decoded += part.decode(encoding or "utf-8", errors="replace")
        else:
            decoded += part

    return decoded


def get_message_body(msg):
    body_parts = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                continue

            if content_type in ("text/plain", "text/html"):
                payload = part.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode(errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body_parts.append(payload.decode(errors="replace"))

    return "\n".join(body_parts)


def extract_verification_code(text):
    text = re.sub(r"=\r?\n", "", text)
    text = re.sub(r"=3D", "=", text, flags=re.IGNORECASE)

    text = re.sub(
        r"=([A-Fa-f0-9]{2})",
        lambda match: chr(int(match.group(1), 16)),
        text,
    )

    patterns = [
        r"verification code below:\s*.*?<span[^>]*>\s*(\d{4,8})\s*</span>",
        r"<span[^>]*font-size\s*:\s*(?:[3-9]\d|\d{3,})px[^>]*>\s*(\d{4,8})\s*</span>",
        r"\b(\d{4,8})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)

    return None


def send_to_discord(code):
    message = f"🎋 **Bambu Lab Verification Code**\n\n```{code}```"

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message},
        timeout=10,
    )

    response.raise_for_status()


def process_inbox():
    mail = imaplib.IMAP4_SSL(EMAIL_URL)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("INBOX")

    status, data = mail.search(None, "UNSEEN")

    if status != "OK" or not data[0]:
        mail.logout()
        # print("No unread emails found.")
        return

    for email_id in data[0].split():
        status, msg_data = mail.fetch(email_id, "(RFC822)")

        if status != "OK":
            print(f"Failed to fetch email ID {email_id.decode()}")
            continue

        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_header_value(msg.get("Subject", "")).strip()

        if subject != TARGET_SUBJECT:
            print(f"Skipping email with subject: {subject}")
            continue

        body = get_message_body(msg)
        code = extract_verification_code(body)

        if not code:
            print("Matched email, but no verification code found.")
            continue

        send_to_discord(code)

        mail.store(email_id, "+FLAGS", "\\Seen")
        print(f"Sent code to Discord: {code}")

    mail.logout()


def validate_env():
    missing = []

    for key, value in {
        "EMAIL_USER": EMAIL_USER,
        "EMAIL_PASS": EMAIL_PASS,
        "EMAIL_URL": EMAIL_URL,
        "DISCORD_WEBHOOK_URL": DISCORD_WEBHOOK_URL,
    }.items():
        if not value:
            missing.append(key)

    if missing:
        raise ValueError(f"Missing required .env values: {', '.join(missing)}")


if __name__ == "__main__":
    validate_env()
    process_inbox()
