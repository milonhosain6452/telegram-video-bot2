import os
import sqlite3
import string
import random
import threading
import time
from flask import Flask, request
from pyrogram import Client, filters
from drive_backup import backup_database  # Google Drive Auto Backup

# ------------------ BOT CREDENTIALS ------------------ #
API_ID = 18088290
API_HASH = "1b06cbb45d19188307f10bcf275341c5"
BOT_TOKEN = "7628770960:AAHKgUwOAtrolkpN4hU58ISbsZDWyIP6324"
CHANNEL_ID = -1002899840201
BOT_USERNAME = "video12321_bot"
OWNER_ID = 6362194288  # Only you can use /checkbackup

# ------------------ INIT ------------------ #
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = Flask(__name__)

# ------------------ DB SETUP ------------------ #
def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.execute("CREATE TABLE IF NOT EXISTS links (code TEXT, message_id INTEGER, user_id INTEGER)")
    conn.commit()
    conn.close()

init_db()

# ------------------ HELPERS ------------------ #
def generate_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def auto_delete(chat_id, msg_id):
    time.sleep(1800)  # 30 minutes
    try:
        bot.delete_messages(chat_id, msg_id)
    except Exception as e:
        print(f"[Delete Error] {e}")

# ------------------ BOT HANDLERS ------------------ #
@bot.on_message(filters.command("start") & filters.private)
def start_command(client, message):
    user_id = message.from_user.id
    with sqlite3.connect("database.db") as db:
        db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))

    # Check for /start payload
    if len(message.command) > 1 and message.command[1].startswith("video"):
        try:
            msg_id = int(message.command[1].replace("video", ""))
            sent = client.copy_message(chat_id=user_id, from_chat_id=CHANNEL_ID, message_id=msg_id)
            client.send_message(chat_id=user_id, text="🕐 এই ভিডিও / পোস্ট ৩০ মিনিট পর ডিলিট হয়ে যাবে।")
            threading.Thread(target=auto_delete, args=(user_id, sent.id)).start()
        except Exception as e:
            message.reply_text("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
            print(f"[Video Error] {e}")
        return

    message.reply_text("👋 Send me a private channel video link or use /genlink to generate a sharable link.")

@bot.on_message(filters.command("genlink") & filters.private)
def genlink_command(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return message.reply_text("❗ Send like this:\n/genlink <channel post link>")

    link = message.command[1]
    try:
        msg_id = int(link.split("/")[-1])
        code = f"video{msg_id}"
        with sqlite3.connect("database.db") as db:
            db.execute("INSERT INTO links (code, message_id, user_id) VALUES (?, ?, ?)", (code, msg_id, user_id))

        share_link = f"https://t.me/{BOT_USERNAME}?start={code}"
        message.reply_text(f"✅ Your private video link:\n{share_link}")

        # Auto backup
        backup_database()

    except Exception as e:
        message.reply_text("❌ Invalid link or error occurred.")
        print(f"[Genlink Error] {e}")

# ------------------ BACKUP LOG CHECKER ------------------ #
@bot.on_message(filters.command("checkbackup") & filters.private)
def check_backup_status(client, message):
    if message.from_user.id != OWNER_ID:
        return message.reply_text("❌ এই কমান্ড শুধুমাত্র বট মালিক ব্যবহার করতে পারবে।")

    try:
        with open("backup_log.txt", "r") as log_file:
            lines = log_file.readlines()
            if not lines:
                return message.reply_text("❗ কোনো ব্যাকআপ লগ পাওয়া যায়নি।")
            last_line = lines[-1].strip()
            message.reply_text(f"📝 সর্বশেষ ব্যাকআপ স্ট্যাটাস:\n\n{last_line}")
    except FileNotFoundError:
        message.reply_text("❌ এখনো কোনো ব্যাকআপ লগ ফাইল তৈরি হয়নি।")
    except Exception as e:
        message.reply_text(f"⚠️ কিছু একটা ভুল হয়েছে:\n{e}")

# ------------------ FLASK WEB ------------------ #
@app.route("/")
def home():
    return "✅ Bot is Live."

@app.route("/<code>")
def handle_link(code):
    with sqlite3.connect("database.db") as db:
        result = db.execute("SELECT message_id, user_id FROM links WHERE code = ?", (code,)).fetchone()
    if result:
        msg_id, user_id = result
        try:
            sent = bot.copy_message(chat_id=user_id, from_chat_id=CHANNEL_ID, message_id=msg_id)
            bot.send_message(chat_id=user_id, text="🕐 এই ভিডিও / পোস্ট ৩০ মিনিট পর ডিলিট হয়ে যাবে।")
            threading.Thread(target=auto_delete, args=(user_id, sent.id)).start()
            return "📤 Video sent to your Telegram!"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    else:
        return "❌ Invalid or expired link."

# ------------------ STARTUP ------------------ #
def run_flask():
    app.run(host="0.0.0.0", port=8080)

def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
