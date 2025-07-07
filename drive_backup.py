from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from datetime import datetime

# 📁 ফোল্ডারের ID (তোমার ফোল্ডার লিংক থেকে)
FOLDER_ID = "10M_NNCugieC42CA6FRWvvE9IEtMeRLzD"

def authorize_drive():
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
        drive = authorize_drive()
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        db_file = "database.db"
        backup_name = f"database_{now}.db"

        if not os.path.exists(db_file):
            raise Exception("database.db not found!")

        file = drive.CreateFile({'title': backup_name, 'parents': [{'id': FOLDER_ID}]})
        file.SetContentFile(db_file)
        file.Upload()

        with open("backup_log.txt", "a") as log:
            log.write(f"[{now}] ✅ Backup done: {backup_name}\n")
    except Exception as e:
        with open("backup_log.txt", "a") as log:
            log.write(f"[{datetime.now().strftime('%Y-%m-%d_%H-%M')}] ❌ Backup failed: {e}\n")

def restore_database(filename="latest"):
    try:
        drive = authorize_drive()
        file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()

        if not file_list:
            raise Exception("No backup files found.")

        if filename == "latest":
            # Latest file by name sort
            file_list.sort(key=lambda x: x['title'], reverse=True)
            selected_file = file_list[0]
        else:
            # Match filename
            selected_file = next((f for f in file_list if f['title'] == filename), None)
            if not selected_file:
                raise Exception(f"File '{filename}' not found in folder.")

        selected_file.GetContentFile("database.db")
        return f"✅ Restore successful from: {selected_file['title']}"
    except Exception as e:
        return f"❌ Restore failed: {e}"

def list_backups():
    try:
        drive = authorize_drive()
        file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false"}).GetList()
        return sorted([f['title'] for f in file_list], reverse=True)
    except Exception as e:
        return [f"❌ Error: {e}"]
