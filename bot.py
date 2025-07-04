import os
import sqlite3
import string
import random
import threading
import time
from flask import Flask
from pyrogram import Client, filters

API_ID = 18088290
API_HASH = "1b06cbb45d19188307f10bcf275341c5"
BOT_TOKEN = "8154600064:AAF5wHjPAnCUYII2Fp3XleRTtUMcUzr2M9g"
CHANNEL_ID = -1002899840201
BOT_USERNAME = "video12321_bot"

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.execute("CREATE TABLE IF NOT EXISTS links (code TEXT PRIMARY KEY, message_id INTEGER, user_id INTEGER)")
    conn.commit()
    conn.close()

init_db()

def generate_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@bot.on_message(filters.command("start") & filters.private)
def start(client, message):
    args = message.text.split()
    if len(args) == 2 and args[1].startswith("video"):
        try:
            msg_id = int(args[1].replace("video", ""))
            sent = client.send_video(chat_id=message.chat.id, from_chat_id=CHANNEL_ID, message_id=msg_id)
            threading.Thread(target=auto_delete, args=(message.chat.id, sent.id)).start()
        except Exception as e:
            message.reply_text("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
            print(e)
    else:
        message.reply_text("👋 Send me a channel video link or use /genlink")

@bot.on_message(filters.command("genlink") & filters.private)
def genlink(client, message):
    if len(message.command) < 2:
        return message.reply_text("❗ Use like this:\n`/genlink https://t.me/c/2899840201/123`", quote=True)
    try:
        link = message.command[1]
        message_id = int(link.split("/")[-1])
        code = generate_code()
        with sqlite3.connect("database.db") as db:
            db.execute("INSERT INTO links (code, message_id, user_id) VALUES (?, ?, ?)", (code, message_id, message.from_user.id))
        deep_link = f"https://t.me/{BOT_USERNAME}?start=video{message_id}"
        message.reply_text(f"✅ Your private video link:\n{deep_link}")
    except Exception as e:
        message.reply_text("❌ Invalid link.")
        print(e)

def auto_delete(chat_id, msg_id):
    time.sleep(1800)
    try:
        bot.delete_messages(chat_id, msg_id)
    except Exception as e:
        print(f"[delete error] {e}")

@app.route("/")
def home():
    return "✅ Bot is running!"

def auto_backup_loop():
    while True:
        os.system("python3 drive_backup.py")
        print("✅ Auto backup complete.")
        time.sleep(3600)

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=auto_backup_loop).start()
    run_bot()
