import os
import imaplib
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")

print("Connecting to:", EMAIL_HOST)

mail = imaplib.IMAP4_SSL("imap.gmail.com")

mail.login(
    EMAIL_USER,
    EMAIL_PASS
)

print("Login successful")
mail.logout()
