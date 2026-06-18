import imaplib
import email
import json
import asyncio
import websockets
from email.header import decode_header
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")


def clean_header(value):
    decoded = decode_header(value)[0]
    text, encoding = decoded
    if isinstance(text, bytes):
        return text.decode(encoding or "utf-8", errors="replace")
    return text


def get_latest_email():
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    status, data = mail.search(None, "UNSEEN")
    if status != "OK" or not data[0]:
        return None

    latest_id = data[0].split()[-1]
    status, msg_data = mail.fetch(latest_id, "(RFC822)")

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    subject = clean_header(msg.get("Subject", ""))
    sender = msg.get("From", "")

    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors="replace")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="replace")

    mail.store(latest_id, "+FLAGS", "\\Seen")
    mail.logout()

    return {
        "subject": subject,
        "from": sender,
        "body": body.strip()
    }


async def send_to_websocket(payload):
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        await websocket.send(json.dumps(payload))
        response = await websocket.recv()
        print("WebSocket response:", response)


async def main():
    email_data = get_latest_email()

    if not email_data:
        print("No unread emails found.")
        return

    payload = {
        "event": "new_email",
        "data": email_data
    }

    await send_to_websocket(payload)


if __name__ == "__main__":
    asyncio.run(main())
