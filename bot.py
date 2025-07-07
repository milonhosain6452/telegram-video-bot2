from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from drive_backup import backup_database, restore_database, list_backups
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
                await message.reply_text("⚠️ এই ভিডিও / পোস্ট ৩০ মিনিট পর ডিলিট হয়ে যাবে\n⚠️ This video/post will be deleted after 30 minutes.", quote=True)
                threading.Timer(1800, lambda: bot.delete_messages(message.chat.id, sent.id)).start()
            except Exception:
                await message.reply("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
        else:
            await message.reply("❌ ভিডিও লিংক পাওয়া যায়নি।")
    else:
        await message.reply("🫵 Send me a channel video link only.", quote=True)

@bot.on_message(filters.command("checkbackup"))
async def check_backup(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    if os.path.exists("backup_log.txt"):
        with open("backup_log.txt", "r") as log:
            lines = log.readlines()[-5:]
        await message.reply("📦 Last backup logs:\n" + "".join(lines))
    else:
        await message.reply("❌ No backup log found.")

@bot.on_message(filters.command("restoredb"))
async def restore_db(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        filename = parts[1] if len(parts) > 1 else "latest"
        result = restore_database(filename)
        await message.reply(result)
    except Exception as e:
        await message.reply(f"❌ Restore failed: {e}")

@bot.on_message(filters.command("listbackups"))
async def list_db_files(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    files = list_backups()
    if not files:
        await message.reply("❌ No backups found.")
    else:
        await message.reply("🗃️ Available backups:\n\n" + "\n".join(files))

@bot.on_message(filters.command("admin"))
async def admin_panel(client, message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("📦 Check Backup", callback_data="checkbackup")],
        [InlineKeyboardButton("🔄 Restore Latest", callback_data="restore_latest")],
        [InlineKeyboardButton("📃 List Backups", callback_data="listbackups")]
    ]
    await message.reply("🛠 Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))

@bot.on_callback_query()
async def cb_handler(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != ADMIN_ID:
        return await callback_query.answer("⛔ Only admin can use this.")
    
    if callback_query.data == "checkbackup":
        if os.path.exists("backup_log.txt"):
            with open("backup_log.txt", "r") as log:
                lines = log.readlines()[-5:]
            await callback_query.message.edit_text("📦 Last backups:\n" + "".join(lines))
        else:
            await callback_query.message.edit_text("❌ No backup log found.")

    elif callback_query.data == "restore_latest":
        result = restore_database("latest")
        await callback_query.message.edit_text(result)

    elif callback_query.data == "listbackups":
        files = list_backups()
        if not files:
            await callback_query.message.edit_text("❌ No backup files.")
        else:
            await callback_query.message.edit_text("🗃️ Available backups:\n\n" + "\n".join(files))

# Flask Keep-Alive (Render/UptimeRobot)
def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()
bot.run()
