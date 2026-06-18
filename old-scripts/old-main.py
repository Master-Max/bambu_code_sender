import os
import json
import asyncio
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import websockets


load_dotenv()

EMAIL_URL = os.getenv("EMAIL_URL")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")


def decode_mime_header(value):
    if not value:
        return ""

    decoded_parts = decode_header(value)
    decoded_string = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_string += part.decode(encoding or "utf-8", errors="replace")
        else:
            decoded_string += part

    return decoded_string


def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(errors="replace")

        return ""

    payload = msg.get_payload(decode=True)
    return payload.decode(errors="replace") if payload else ""


def read_latest_unread_email():
    mail = imaplib.IMAP4_SSL(EMAIL_URL)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    status, data = mail.search(None, "UNSEEN")

    if status != "OK" or not data[0]:
        mail.logout()
        return None

    latest_email_id = data[0].split()[-1]

    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

    if status != "OK":
        mail.logout()
        raise RuntimeError("Failed to fetch email")

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    email_data = {
        "message_id": msg.get("Message-ID", ""),
        "from": decode_mime_header(msg.get("From", "")),
        "to": decode_mime_header(msg.get("To", "")),
        "subject": decode_mime_header(msg.get("Subject", "")),
        "date": msg.get("Date", ""),
        "body": get_email_body(msg).strip()
    }

    mail.store(latest_email_id, "+FLAGS", "\\Seen")
    mail.logout()

    return email_data


async def send_to_websocket(email_data):
    payload = {
        "event": "new_email",
        "source": "gmail_imap",
        "data": email_data
    }

    async with websockets.connect(WEBSOCKET_URL) as websocket:
        await websocket.send(json.dumps(payload))
        print("Email sent to websocket")

        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print("WebSocket response:", response)
        except asyncio.TimeoutError:
            print("No response from websocket")


async def main():
    email_data = read_latest_unread_email()

    if not email_data:
        print("No unread emails found.")
        return

    await send_to_websocket(email_data)


if __name__ == "__main__":
    asyncio.run(main())
