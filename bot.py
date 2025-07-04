import os
import sqlite3
import string
import random
import threading
import time
from flask import Flask
from pyrogram import Client, filters
from drive_backup import backup_database  # ⬅️ Google Drive Backup Function

# Credentials
API_ID = 18088290
API_HASH = "1b06cbb45d19188307f10bcf275341c5"
BOT_TOKEN = "8154600064:AAF5wHjPAnCUYII2Fp3XleRTtUMcUzr2M9g"
CHANNEL_ID = -1002899840201
BOT_USERNAME = "video12321_bot"  # Change to your bot username (without @)

# Init bot & flask
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.execute("CREATE TABLE IF NOT EXISTS links (code TEXT, message_id INTEGER, user_id INTEGER)")
    conn.commit()
    conn.close()

init_db()

# Unique link generator
def generate_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# /start command
@bot.on_message(filters.command("start") & filters.private)
def start(client, message):
    user_id = message.from_user.id
    with sqlite3.connect("database.db") as db:
        db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    if len(message.command) > 1 and message.command[1].startswith("video"):
        msg_id = int(message.command[1].replace("video", ""))
        try:
            sent = client.copy_message(chat_id=user_id, from_chat_id=CHANNEL_ID, message_id=msg_id)
            client.send_message(user_id, "⚠️ এই ভিডিও / পোস্ট ৩০ মিনিট পর ডিলিট হয়ে যাবে।")
            threading.Thread(target=auto_delete, args=(user_id, sent.id)).start()
        except Exception as e:
            message.reply_text("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
    else:
        message.reply_text("👋 Send me a channel video link or use /genlink to generate a sharable link.")

# /genlink command
@bot.on_message(filters.command("genlink") & filters.private)
def genlink(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return message.reply_text("❗ Send like this:\n/genlink <channel post link>")
    link = message.command[1]
    try:
        message_id = int(link.split("/")[-1])
        code = f"video{message_id}"
        with sqlite3.connect("database.db") as db:
            db.execute("INSERT INTO links (code, message_id, user_id) VALUES (?, ?, ?)", (code, message_id, user_id))
        share_link = f"https://t.me/{BOT_USERNAME}?start={code}"
        message.reply_text(f"✅ Your private video link:\n{share_link}")
        backup_database()  # ⬅️ Auto backup after generating link
    except Exception as e:
        message.reply_text("❌ Invalid link. Try again.")
        print(e)

# Auto delete function
def auto_delete(chat_id, msg_id):
    time.sleep(1800)  # 30 minutes
    try:
        bot.delete_messages(chat_id, msg_id)
    except Exception as e:
        print(f"[delete error] {e}")

# Flask route for uptime
@app.route("/")
def home():
    return "✅ Bot is Live."

# Run both bot & flask
def run_flask():
    app.run(host="0.0.0.0", port=8080)

def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()
