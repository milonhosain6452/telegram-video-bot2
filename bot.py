from pyrogram import Client, filters from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton from pyrogram.enums import ParseMode from drive_backup import backup_database, restore_database import sqlite3 import time import re import os import threading from flask_app import app

API_ID = 18088290 API_HASH = "1b06cbb45d19188307f10bcf275341c5" BOT_TOKEN = "8154600064:AAGIreAz9oG_3Ypbrga3VLFSITbx4qvKM6A" CHANNEL_ID = -1002899840201 ADMIN_ID = 6362194288

bot = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

Ensure database exists only if not already restored

if not os.path.exists("database.db"): conn = sqlite3.connect("database.db") conn.execute('''CREATE TABLE IF NOT EXISTS videos (msg_id INTEGER PRIMARY KEY, unique_code TEXT NOT NULL);''') conn.commit() conn.close()

@bot.on_message(filters.command("start")) async def start(client, message: Message): if len(message.command) > 1 and message.command[1].startswith("video"): code = message.command[1].replace("video", "") conn = sqlite3.connect("database.db") cursor = conn.cursor() cursor.execute("SELECT msg_id FROM videos WHERE unique_code=?", (code,)) result = cursor.fetchone() conn.close()

if result:
        try:
            sent = await bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=result[0]
            )
            await message.reply_text(
                "⚠️ এই ভিডিও / পোস্ট ৩০ মিনিট পরে মুছে যাবে\n\n⚠️ This video/post will auto-delete after 30 minutes",
                quote=True
            )
            threading.Timer(1800, lambda: bot.delete_messages(message.chat.id, sent.id)).start()
        except Exception as e:
            await message.reply("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
    else:
        await message.reply("❌ ভিডিও লিংক পাওয়া যায়নি।")
else:
    await message.reply("👋 শুধু ভিডিও লিংক পাঠান।")

@bot.on_message(filters.command("genlink") & filters.user(ADMIN_ID)) async def genlink(client, message: Message): if not message.reply_to_message and len(message.command) < 2: await message.reply("⚠️ একটি চ্যানেলের ভিডিও/পোস্টের লিংক দিন। যেমন: /genlink https://t.me/c/2899840201/28", quote=True) return

link = message.text.split(" ", 1)[1] if len(message.command) > 1 else ""
match = re.search(r"/c/(\d+)/(\d+)", link)

if match:
    msg_id = int(match.group(2))
    unique_code = f"{msg_id}"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO videos (msg_id, unique_code) VALUES (?, ?)", (msg_id, unique_code))
    conn.commit()
    conn.close()

    share_link = f"https://t.me/{bot.me.username}?start=video{unique_code}"
    await message.reply(f"✅ Generated Link:\n{share_link}", quote=True)
    backup_database()
else:
    await message.reply("❌ ভুল লিংক ফরম্যাট। লিংক হওয়া উচিত: `https://t.me/c/<channel_id>/<message_id>`", quote=True)

@bot.on_message(filters.command("checkbackup") & filters.user(ADMIN_ID)) async def check_backup(client, message: Message): if os.path.exists("backup_log.txt"): with open("backup_log.txt", "r") as log: last_lines = log.readlines()[-5:] await message.reply("📦 Last backup logs:\n\n" + "".join(last_lines)) else: await message.reply("❌ No backup log found.")

@bot.on_message(filters.command("restoredb") & filters.user(ADMIN_ID)) async def restoredb_command(client, message: Message): try: parts = message.text.split(" ", 1) filename = parts[1] if len(parts) > 1 else None result = restore_database(filename) await message.reply(f"✅ Restore successful from: {result}") except Exception as e: await message.reply(f"❌ Restore failed:\n{e}")

@bot.on_message(filters.command("admin") & filters.user(ADMIN_ID)) async def admin_panel(client, message: Message): keyboard = [ [InlineKeyboardButton("📦 Check Backup", callback_data="checkbackup")], [InlineKeyboardButton("🔄 Restore Latest", callback_data="restore_latest")] ] await message.reply("🔧 Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))

@bot.on_callback_query() async def callback_handler(client, callback_query): if callback_query.from_user.id != ADMIN_ID: return await callback_query.answer("⛔️ Access denied.", show_alert=True)

data = callback_query.data
if data == "checkbackup":
    if os.path.exists("backup_log.txt"):
        with open("backup_log.txt", "r") as log:
            last_lines = log.readlines()[-5:]
            await callback_query.message.edit_text("📦 Last backup logs:\n\n" + "".join(last_lines))
    else:
        await callback_query.message.edit_text("❌ No backup log found.")
elif data == "restore_latest":
    try:
        result = restore_database()
        await callback_query.message.edit_text(f"✅ Restore successful from: {result}")
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Restore failed:\n{e}")

🔄 Flask Keep-Alive (Render / Replit)

def run_flask(): app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

bot.run()
