#!/usr/bin/env python3
"""One-time OAuth consent to mint a token with the Google Ads (`adwords`) scope.

Reuses the existing installed-app OAuth client (credentials/Google Creds.json).
Run once in a browser; writes credentials/token_gads.json (gitignored).

    python3 scripts/gads_oauth_consent.py
"""
import json
import pathlib
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLIENT = ROOT / "credentials" / "Google Creds.json"
OUT = ROOT / "credentials" / "token_gads.json"
SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main() -> None:
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), scopes=SCOPES)
    # Opens a browser; falls back to console if no browser is available.
    creds = flow.run_local_server(port=0, prompt="consent")
    OUT.write_text(
        json.dumps(
            {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": list(creds.scopes),
            },
            indent=2,
        )
    )
    print(f"Wrote {OUT}")
    print("refresh_token present:", bool(creds.refresh_token))


if __name__ == "__main__":
    main()
