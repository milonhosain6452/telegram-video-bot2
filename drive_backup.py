from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import datetime

def backup_database():
    try:
        # Authenticate
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
        log_file = "backup_log.txt"
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not os.path.exists(db_file):
            print("❌ database.db not found!")
            with open(log_file, "a") as log:
                log.write(f"[{now}] ❌ Backup failed: database.db not found!\n")
            return

        # Delete previous
        for file in drive.ListFile({'q': f"title='{db_file}' and trashed=false"}).GetList():
            file.Delete()

        # Upload new
        uploaded = drive.CreateFile({'title': db_file})
        uploaded.SetContentFile(db_file)
        uploaded.Upload()

        print("✅ database.db uploaded to Google Drive!")
        with open(log_file, "a") as log:
            log.write(f"[{now}] ✅ Backup done: {db_file}\n")

    except Exception as e:
        print("❌ Backup failed:", e)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open("backup_log.txt", "a") as log:
            log.write(f"[{now}] ❌ Backup failed: {str(e)}\n")
