import os
import sqlite3
import string
import random
import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message
from drive_backup import backup_database

# BOT CONFIG
API_ID = 18088290
API_HASH = "1b06cbb45d19188307f10bcf275341c5"
BOT_TOKEN = "8154600064:AAGXBf6Rlk8aIqQohHSC8yxCrqgGnkouXKk"
CHANNEL_ID = -1002899840201
OWNER_ID = 6362194288  # তোমার ইউজার আইডি

bot = Client("video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# database
conn = sqlite3.connect("database.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY AUTOINCREMENT, msg_id INTEGER, unique_id TEXT)")
conn.commit()


def generate_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


@bot.on_message(filters.command("genlink") & filters.private)
async def genlink(client, message: Message):
    if not message.from_user:
        return
    if len(message.command) < 2:
        await message.reply("❌ Please send a valid video link like:\n`/genlink https://t.me/c/2899840201/28`")
        return

    try:
        link = message.command[1]
        if "/c/" not in link:
            return await message.reply("❌ Invalid link format.")

        msg_id = int(link.split("/")[-1])
        unique_id = f"video{msg_id}"
        c.execute("INSERT INTO links (msg_id, unique_id) VALUES (?, ?)", (msg_id, unique_id))
        conn.commit()
        share_link = f"https://t.me/{bot.me.username}?start={unique_id}"
        await message.reply(f"✅ Your private video link:\n{share_link}")

        backup_database()  # auto backup after link gen

    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    if not message.from_user:
        return

    args = message.text.split(" ", 1)
    if len(args) == 2 and args[1].startswith("video"):
        try:
            msg_id = int(args[1][5:])
            c.execute("SELECT msg_id FROM links WHERE unique_id = ?", (args[1],))
            row = c.fetchone()
            if not row:
                return await message.reply("❌ Video not found or expired.")

            sent = await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id,
                caption="⏳ This video/post will be deleted after 30 minutes."
            )

            await asyncio.sleep(1800)
            await sent.delete()

        except Exception as e:
            await message.reply("❌ ভিডিও আনতে সমস্যা হচ্ছে।")
    else:
        await message.reply("👋 Send me a private channel video link or use /genlink <link>.")


@bot.on_message(filters.command("backup") & filters.user(OWNER_ID))
async def manual_backup(client, message: Message):
    try:
        backup_database()
        await message.reply("✅ Manual backup done and uploaded to Google Drive!")
    except Exception as e:
        await message.reply(f"❌ Backup failed: {e}")


print("✅ Bot is running...")
bot.run()
