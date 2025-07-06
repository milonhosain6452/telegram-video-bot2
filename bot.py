from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
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
BOT_TOKEN = "8154600064:AAGIreAz9oG_3Ypbrga3VLFSITbx4qvKM6A"
CHANNEL_ID = -1002899840201
ADMIN_ID = 6362194288

bot = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Database check
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
                await message.reply_text("⚠️ এই ভিডিও / পোস্ট ৩০ মিনিট পর ডিলিট হয়ে যাবে\n⚠️ This video/post will be deleted after 30 minutes", quote=True)
                time.sleep(2)
                threading.Timer(1800, lambda: bot.delete_messages(message.chat.id, sent.id)).start()
            except Exception as e:
                await message.reply("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
        else:
            await message.reply("❌ ভিডিও লিংক পাওয়া যায়নি।")

    else:
        if message.from_user.id == ADMIN_ID:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📽 Generate Link", switch_inline_query_current_chat="/genlink")],
                [InlineKeyboardButton("✅ Check Backup", callback_data="check_backup")],
                [InlineKeyboardButton("♻️ Restore DB", callback_data="restore_db")],
                [InlineKeyboardButton("🔗 Shorten Link", switch_inline_query_current_chat="/short")],
                [InlineKeyboardButton("▶️ Start Help", callback_data="start_help")]
            ])
            await message.reply("👋 Welcome Admin! Use the buttons below:", reply_markup=keyboard)
        else:
            await message.reply("👋 Send me a channel video link or use /genlink to generate a sharable link.")

@bot.on_message(filters.command("genlink"))
async def genlink(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        await message.reply("⚠️ একটি চ্যানেলের ভিডিও/পোস্টের লিংক দাও।\nযেমন: `/genlink https://t.me/c/2899840201/28`", quote=True)
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

@bot.on_message(filters.command("restoredb"))
async def restore_db(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔️ Only admin can use this command.")

    try:
        from drive_backup import restore_database
        restore_database()
        await message.reply("✅ Database restored from Google Drive!")
    except Exception as e:
        await message.reply(f"❌ Restore failed:\n{e}")

@bot.on_message(filters.command("short"))
async def shorten_link(client, message: Message):
    if not message.text or len(message.text.split()) < 2:
        return await message.reply("⚠️ Provide a link to shorten.\nUsage: `/short https://example.com`")
    try:
        import requests
        url = message.text.split(" ", 1)[1]
        api_token = "87dfd72cea81178fac6d85638785781be0860817"
        res = requests.get(f"https://shrinkearn.com/api?api={api_token}&url={url}")
        data = res.json()
        if "shortenedUrl" in data:
            await message.reply(f"🔗 Short Link:\n{data['shortenedUrl']}")
        else:
            await message.reply(f"❌ Error:\n{data}")
    except Exception as e:
        await message.reply(f"❌ API Error:\n{e}")

# Callback button handler
@bot.on_callback_query()
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != ADMIN_ID:
        return await callback_query.answer("⛔️ Only admin can use this.")

    if callback_query.data == "check_backup":
        await check_backup(client, callback_query.message)
    elif callback_query.data == "restore_db":
        await restore_db(client, callback_query.message)
    elif callback_query.data == "start_help":
        await callback_query.message.reply("ℹ️ Use /genlink to generate video links, /short to shorten links, /checkbackup to check logs, and /restoredb to recover DB.")

# Flask keep alive
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()
bot.run()
