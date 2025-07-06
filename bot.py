from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from drive_backup import backup_database
import sqlite3
import time
import re
import os
import threading
import requests
from flask_app import app

API_ID = 18088290
API_HASH = "1b06cbb45d19188307f10bcf275341c5"
BOT_TOKEN = "8154600064:AAGbTUnRLj0A0ZzDyM5AUNPT3rGw8FwZ-M8"
CHANNEL_ID = -1002899840201
ADMIN_ID = 6362194288
SHORT_API = "87dfd72cea81178fac6d85638785781be0860817"

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
                threading.Timer(1800, lambda: bot.delete_messages(message.chat.id, sent.id)).start()
            except Exception as e:
                await message.reply("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
        else:
            await message.reply("❌ ভিডিও লিংক পাওয়া যায়নি।")
    else:
        if message.from_user.id == ADMIN_ID:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Check Backup", callback_data="checkbackup")],
                [InlineKeyboardButton("♻️ Restore Database", callback_data="restoredb")]
            ])
            await message.reply("👋 Admin Panel:", reply_markup=keyboard)
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

@bot.on_message(filters.command("short"))
async def short_link(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("🔗 একটা লিংক দাও শর্ট করার জন্য।\nযেমন: `/short https://yourlink.com`")

    original_link = message.text.split(" ", 1)[1]
    api_url = f"https://shrinkearn.com/api?api={SHORT_API}&url={original_link}"

    try:
        res = requests.get(api_url).json()
        if "shortenedUrl" in res:
            await message.reply(f"✅ Shortened Link:\n{res['shortenedUrl']}")
        else:
            await message.reply(f"❌ API তে সমস্যা হচ্ছে:\n{res}")
    except Exception as e:
        await message.reply(f"❌ API তে সমস্যা হচ্ছে:\n{e}")

@bot.on_callback_query()
async def handle_buttons(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != ADMIN_ID:
        return await callback_query.answer("⛔️ Only admin can use this!", show_alert=True)

    if callback_query.data == "checkbackup":
        if os.path.exists("backup_log.txt"):
            with open("backup_log.txt", "r") as log:
                last_lines = log.readlines()[-5:]
                await callback_query.message.reply("📦 Last backup logs:\n\n" + "".join(last_lines))
        else:
            await callback_query.message.reply("❌ No backup log found.")

    elif callback_query.data == "restoredb":
        await callback_query.message.reply("♻️ Restore ফিচার খুব শীঘ্রই যুক্ত করা হবে ইনশাআল্লাহ!")

# ✅ Flask Keep-Alive (Render & UptimeRobot support)
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# 🔃 Run the bot
bot.run()
