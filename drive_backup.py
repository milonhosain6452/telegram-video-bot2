from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import datetime

BACKUP_FOLDER_ID = "10M_NNCugieC42CA6FRWvvE9IEtMeRLzD"  # Replace with your folder ID

def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()
    gauth.SaveCredentialsFile("mycreds.txt")
    return GoogleDrive(gauth)

def backup_database():
    try:
        drive = authenticate_drive()
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_file_name = f"database_{now}.db"
        log_file = "backup_log.txt"

        if not os.path.exists("database.db"):
            print("❌ database.db not found!")
            with open(log_file, "a") as log:
                log.write(f"[{now}] ❌ Backup failed: database.db not found!\n")
            return

        file_to_upload = drive.CreateFile({
            'title': backup_file_name,
            'parents': [{'id': BACKUP_FOLDER_ID}]
        })
        file_to_upload.SetContentFile("database.db")
        file_to_upload.Upload()

        print("✅ database.db uploaded to Google Drive as", backup_file_name)
        with open(log_file, "a") as log:
            log.write(f"[{now}] ✅ Backup done: {backup_file_name}\n")

    except Exception as e:
        print("❌ Backup failed:", e)
        with open("backup_log.txt", "a") as log:
            log.write(f"[{now}] ❌ Backup failed: {str(e)}\n")

def restore_database():
    try:
        drive = authenticate_drive()
        file_list = drive.ListFile({
            'q': f"'{BACKUP_FOLDER_ID}' in parents and trashed=false and title contains 'database_'"
        }).GetList()

        if not file_list:
            raise Exception("❌ No backup files found in Google Drive folder.")

        latest_file = sorted(file_list, key=lambda f: f['title'], reverse=True)[0]
        latest_file.GetContentFile("database.db")
        print(f"✅ Restored from: {latest_file['title']}")

    except Exception as e:
        raise e
