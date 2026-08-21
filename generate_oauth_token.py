import json
import os
import sys
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "your_client_id_here")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "your_client_secret_here")

SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]

if CLIENT_ID == "your_client_id_here" or CLIENT_SECRET == "your_client_secret_here":
    print("ERROR: Please specify OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET in your .env file!", file=sys.stderr)
    sys.exit(1)

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
creds = flow.run_local_server(port=0, prompt="consent")

print("\n" + "="*50)
print("SUCCESS! YOUR OAUTH REFRESH TOKEN IS:")
print(creds.refresh_token)
print("="*50 + "\n")
