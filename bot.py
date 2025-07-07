from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from drive_backup import backup_database, restore_database
import sqlite3
import time
import re
import os
import threading
import requests
from flask_app import app

API_ID = 18088290
API_HASH = "1b06cbb45d19188307f10bcf275341c5"
BOT_TOKEN = "8154600064:AAGIreAz9oG_3Ypbrga3VLFSITbx4qvKM6A"
CHANNEL_ID = -1002899840201
ADMIN_ID = 6362194288
SHORT_API = "87dfd72cea81178fac6d85638785781be0860817"

bot = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
                await message.reply_text(
                    "⚠️ পোস্ট / ভিডিও ৩০ মিনিট পর ডিলিট হবে\n⚠️ Post/Video will be deleted after 30 minutes.",
                    quote=True
                )
                threading.Timer(1800, lambda: bot.delete_messages(message.chat.id, sent.id)).start()
            except Exception:
                await message.reply("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
        else:
            await message.reply("❌ ভিডিও লিংক পাওয়া যায়নি।")
    else:
        await message.reply(
            "👋 শুধু ভিডিও দেখতে পারবে।",
            quote=True
        )

@bot.on_message(filters.command("genlink"))
async def genlink(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔️ You are not allowed to generate links.")

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

        share_link = f"https://t.me/{(await bot.get_me()).username}?start=video{unique_code}"
        await message.reply(f"✅ Your private video link:\n{share_link}", quote=True)
        backup_database()

    else:
        await message.reply("❌ ভুল লিংক ফরম্যাট। লিংকটি এমন হওয়া উচিত:\n`https://t.me/c/<channel_id>/<message_id>`", quote=True)

@bot.on_message(filters.command("short"))
async def short_link(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔️ You are not authorized to shorten links.")

    if len(message.command) < 2:
        return await message.reply("⚠️ লিংক দিন শর্ট করার জন্য।\n\nযেমন: `/short https://example.com`")

    long_url = message.text.split(" ", 1)[1]

    try:
        api = SHORT_API
        res = requests.get(f"https://shrinkearn.com/api?api={api}&url={long_url}")
        data = res.json()

        if "shortenedUrl" in data:
            await message.reply(f"✅ Shortened URL:\n{data['shortenedUrl']}")
        else:
            await message.reply(f"❌ শর্ট করতে সমস্যা:\n{data.get('message', 'Unknown error')}")
    except Exception as e:
        await message.reply(f"❌ Request error:\n{e}")

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

@bot.on_message(filters.command("restoredb"))
async def restore_db(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔️ You are not authorized to restore.")

    try:
        file_name = None
        if len(message.command) > 1:
            file_name = message.command[1]
        restore_database(file_name)
        msg = f"✅ Restore successful{f' from: {file_name}' if file_name else ''}."
        await message.reply(msg)
    except Exception as e:
        await message.reply(f"❌ Restore failed:\n{e}")

@bot.on_message(filters.command("admin"))
async def admin_menu(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    buttons = [
        [InlineKeyboardButton("🔁 Restore", callback_data="restoredb")],
        [InlineKeyboardButton("📦 Check Backup", callback_data="checkbackup")],
    ]
    await message.reply("🔐 Admin Panel:", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    if callback_query.from_user.id != ADMIN_ID:
        return await callback_query.answer("Unauthorized", show_alert=True)

    if callback_query.data == "checkbackup":
        if os.path.exists("backup_log.txt"):
            with open("backup_log.txt", "r") as log:
                last_lines = log.readlines()[-5:]
                await callback_query.message.reply("📦 Last backup logs:\n\n" + "".join(last_lines))
        else:
            await callback_query.message.reply("❌ No backup log found.")

    elif callback_query.data == "restoredb":
        try:
            restore_database()
            await callback_query.message.reply("✅ Restore successful.")
        except Exception as e:
            await callback_query.message.reply(f"❌ Restore failed:\n{e}")

# 🟢 Flask Keep-Alive
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# 🚀 Run Bot
bot.run()
