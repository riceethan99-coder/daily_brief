# gmail_auth.py
# Run this ONCE locally to get your Gmail OAuth2 refresh token:
#
#   python gmail_auth.py
#
# Your browser will open, you'll log in with your Gmail account and grant
# access. The terminal will then print your GMAIL_REFRESH_TOKEN.
# Copy it into your .env file and add it as a GitHub secret.
#
# Prerequisites (add to .env before running):
#   GMAIL_CLIENT_ID     — from Google Cloud Console (OAuth 2.0 Desktop app)
#   GMAIL_CLIENT_SECRET — from Google Cloud Console

import os
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    load_dotenv(Path(__file__).parent / ".env")

    client_id = os.environ["GMAIL_CLIENT_ID"]
    client_secret = os.environ["GMAIL_CLIENT_SECRET"]

    # Build config dict — same structure as a downloaded credentials.json,
    # but constructed from env vars so no file needs to be committed.
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    # port=0 lets the OS pick any free port — avoids port-conflict errors
    credentials = flow.run_local_server(port=0)

    print("\n--- OAuth complete ---")
    print(f"GMAIL_REFRESH_TOKEN={credentials.refresh_token}")
    print("\nCopy the value above into your .env file and GitHub secrets.")


if __name__ == "__main__":
    main()
