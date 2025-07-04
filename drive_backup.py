from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os

def backup_database():
    if not os.path.exists("database.db"):
        print("❌ database.db not found!")
        return

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

    file1 = drive.CreateFile({'title': 'database.db'})
    file1.SetContentFile("database.db")
    file1.Upload()

    print("✅ database.db uploaded to Google Drive!")
