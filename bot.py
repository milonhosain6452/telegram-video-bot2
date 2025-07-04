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
BOT_USERNAME = "video12321_bot"

# Bot & Flask Init
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = Flask(__name__)

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.execute("CREATE TABLE IF NOT EXISTS links (code TEXT, message_id INTEGER, user_id INTEGER)")
    conn.commit()
    conn.close()

init_db()

# --- Code Generator ---
def generate_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# --- Start Command ---
@bot.on_message(filters.command("start") & filters.private)
def start_handler(client, message):
    text = message.text
    user_id = message.from_user.id
    with sqlite3.connect("database.db") as db:
        db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    
    if len(text.split()) == 2 and text.split()[1].startswith("video"):
        try:
            msg_id = int(text.split()[1][5:])
            sent = bot.send_video(chat_id=user_id, from_chat_id=CHANNEL_ID, message_id=msg_id)
            threading.Thread(target=delete_after, args=(user_id, sent.id)).start()
        except Exception as e:
            message.reply_text("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
            print(f"[ERROR] {e}")
    else:
        message.reply_text("👋 Send me a private channel video link using /genlink")

# --- Genlink Command ---
@bot.on_message(filters.command("genlink") & filters.private)
def genlink_handler(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return message.reply_text("❗ Format: /genlink <channel video link>")
    
    link = message.command[1]
    try:
        msg_id = int(link.split("/")[-1])
        code = f"video{msg_id}"
        with sqlite3.connect("database.db") as db:
            db.execute("INSERT INTO links (code, message_id, user_id) VALUES (?, ?, ?)", (code, msg_id, user_id))
        
        # ✅ Backup after every new link
        backup_database()

        start_link = f"https://t.me/{BOT_USERNAME}?start={code}"
        message.reply_text(f"✅ Your private video link:\n{start_link}")
    except Exception as e:
        message.reply_text("❌ Invalid link. Please check.")
        print(e)

# --- Auto Delete ---
def delete_after(chat_id, msg_id):
    time.sleep(1800)  # 30 minutes
    try:
        bot.delete_messages(chat_id, msg_id)
    except Exception as e:
        print(f"[Delete Error] {e}")

# --- Flask ---
@app.route("/")
def home():
    return "✅ Bot is Live."

# --- Run All ---
def run():
    app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run).start()
    bot.run()
