from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

gauth = GoogleAuth()
gauth.LoadCredentialsFile("mycreds.txt")

if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()

gauth.SaveCredentialsFile("mycreds.txt")

drive = GoogleDrive(gauth)

if os.path.exists("database.db"):
    file = drive.CreateFile({'title': 'database.db'})
    file.SetContentFile("database.db")
    file.Upload()
    print("✅ database.db uploaded to Google Drive!")
else:
    print("❌ database.db not found!")
