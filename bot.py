from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from drive_backup import backup_database
import sqlite3
import time
import re
import os
import threading
from flask_app import app

API_ID = 18088290
API_HASH = "1b06cbb45d19188307f10bcf275341c5"
BOT_TOKEN = "8154600064:AAGXBf6Rlk8aIqQohHSC8yxCrqgGnkouXKk"
CHANNEL_ID = -1002899840201
ADMIN_ID = 6362194288

bot = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Ensure database exists
if not os.path.exists("database.db"):
    conn = sqlite3.connect("database.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS videos
                 (msg_id INTEGER PRIMARY KEY,
                 unique_code TEXT NOT NULL);''')
    conn.commit()
    conn.close()

@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    if len(message.command) > 1 and message.command[1].startswith("video"):
        code = message.command[1].replace("video", "")
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT msg_id FROM videos WHERE unique_code=?", (code,))
        result = cursor.fetchone()
        conn.close()

        if result:
            try:
                sent = await bot.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=CHANNEL_ID,
                    message_id=result[0]
                )
                await message.reply_text("⚠️ এই ভিডিও / পোস্ট ৩০ মিনিট পর ডিলিট হয়ে যাবে", quote=True)
                time.sleep(2)

                # Schedule deletion after 30 minutes
                threading.Timer(1800, lambda: bot.delete_messages(message.chat.id, sent.id)).start()
            except Exception as e:
                await message.reply("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
        else:
            await message.reply("❌ ভিডিও লিংক পাওয়া যায়নি।")
    else:
        await message.reply(
            "👋 Send me a channel video link or use /genlink to generate a sharable link."
        )

@bot.on_message(filters.command("genlink"))
async def genlink(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply("⚠️ একটি চ্যানেলের ভিডিও/পোস্টের লিংক দাও।\n\nযেমন: `/genlink https://t.me/c/2899840201/28`", quote=True)
        return

    link = message.text.split(" ", 1)[1] if len(message.command) > 1 else ""
    match = re.search(r"/c/\d+/(\\d+)", link) or re.search(r"/c/(\d+)/(\d+)", link)

    if match:
        msg_id = int(match.group(2))
        unique_code = f"{msg_id}"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO videos (msg_id, unique_code) VALUES (?, ?)", (msg_id, unique_code))
        conn.commit()
        conn.close()

        share_link = f"https://t.me/{bot.me.username}?start=video{unique_code}"
        await message.reply(f"✅ Your private video link:\n{share_link}", quote=True)

        # Optional auto-backup
        backup_database()

    else:
        await message.reply("❌ ভুল লিংক ফরম্যাট। লিংকটি এমন হওয়া উচিত:\n`https://t.me/c/<channel_id>/<message_id>`", quote=True)

@bot.on_message(filters.command("checkbackup"))
async def check_backup(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔️ Only admin can use this command.")

    try:
        if os.path.exists("backup_log.txt"):
            with open("backup_log.txt", "r") as log:
                last_lines = log.readlines()[-5:]
                await message.reply("📦 Last backup logs:\n\n" + "".join(last_lines))
        else:
            await message.reply("❌ No backup log found.")
    except Exception as e:
        await message.reply(f"❌ Error reading log:\n{e}")

# ✅ Flask Keep-Alive (Render & UptimeRobot support)
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# 🔃 Run the bot
bot.run()
