from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import datetime

# Google Drive Folder ID (must be public or shared with the service)
FOLDER_ID = "10M_NNCugieC42CA6FRWvvE9IEtMeRLzD"

def backup_database():
    try:
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

        db_file = "database.db"
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_name = f"database_{now}.db"
        log_file = "backup_log.txt"

        if not os.path.exists(db_file):
            print("❌ database.db not found!")
            with open(log_file, "a") as log:
                log.write(f"[{now}] ❌ Backup failed: database.db not found!\n")
            return

        file_to_upload = drive.CreateFile({
            'title': backup_name,
            'parents': [{'id': FOLDER_ID}]
        })
        file_to_upload.SetContentFile(db_file)
        file_to_upload.Upload()

        print(f"✅ {backup_name} uploaded to Google Drive folder.")
        with open(log_file, "a") as log:
            log.write(f"[{now}] ✅ Backup done: {backup_name}\n")

    except Exception as e:
        print("❌ Backup failed:", e)
        with open("backup_log.txt", "a") as log:
            log.write(f"[{now}] ❌ Backup failed: {str(e)}\n")
