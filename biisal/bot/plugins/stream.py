import os
import asyncio
from asyncio import TimeoutError
from biisal.bot import StreamBot
from biisal.utils.database import Database
from biisal.utils.human_readable import humanbytes
from biisal.vars import Var
from urllib.parse import quote_plus
from pyrogram import filters, Client
from pyrogram.errors import FloodWait, UserNotParticipant, MessageNotModified
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import re

from biisal.utils.file_properties import get_name, get_hash, get_media_file_size

MY_PASS = os.environ.get("MY_PASS", None)
pass_dict = {}
get_file_dict = {}
pass_db = Database(Var.DATABASE_URL, "ag_passwords")

db = Database(Var.DATABASE_URL, Var.name)

msg_text = """<b>‣ ʏᴏᴜʀ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ! 😎

‣ Fɪʟᴇ ɴᴀᴍᴇ : <i>{}</i>
‣ Fɪʟᴇ ꜱɪᴢᴇ : {}

\n‣ ❤️ Powered By : @BoB_Files1✨🫶</b>"""

@StreamBot.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo), group=4)
async def private_receive_handler(c: Client, m: Message):
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id)

    try:
        log_msg = await m.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = f"{Var.URL}watch/{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        online_link = f"{Var.URL}{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

        await m.reply_text(
            text=msg_text.format(get_name(log_msg), humanbytes(get_media_file_size(m))),
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📺 Stream", url=stream_link),
                 InlineKeyboardButton("📥 Download", url=online_link)],
                [InlineKeyboardButton("📂 Get File", callback_data=f"get_file_{log_msg.id}")],
                [InlineKeyboardButton("🔗 Share File", callback_data=f"share_file_{log_msg.id}")]
            ])
        )
    except FloodWait as e:
        print(f"Sleeping for {e.x} seconds due to FloodWait.")
        await asyncio.sleep(e.x)

@StreamBot.on_callback_query(filters.regex(r"get_file_(\d+)"))
async def get_file_button_handler(c: Client, query: CallbackQuery):
    if match := re.search(r"get_file_(\d+)", query.data):
        message_id = int(match.group(1))
        user_id = query.from_user.id  

        file_msg = await c.get_messages(chat_id=Var.BIN_CHANNEL, message_ids=message_id)
        if not file_msg:
            await query.answer("⚠ No File Found!", show_alert=True)
            return
        try:
            await file_msg.copy(chat_id=user_id)
            await query.answer("✅ File sent to your DM!", show_alert=True)
        except Exception as e:
            print(e)
            get_file_dict[user_id] = file_msg
            username = (await c.get_me()).username
            await query.answer("Start Bot In PM First!", show_alert=True)

@StreamBot.on_callback_query(filters.regex(r"share_file_(\d+)"))
async def share_file_button_handler(c: Client, query: CallbackQuery):
    if match := re.search(r"share_file_(\d+)", query.data):
        message_id = int(match.group(1))
        user_id = query.from_user.id

        file_msg = await c.get_messages(chat_id=Var.BIN_CHANNEL, message_ids=message_id)
        if not file_msg:
            await query.answer("⚠ No File Found!", show_alert=True)
            return
        try:
            # Send the file to the user for easy forwarding
            await file_msg.copy(chat_id=user_id)
            await query.answer("✅ File sent! You can now forward it anywhere.", show_alert=True)
        except Exception as e:
            print(e)
            await query.answer("⚠ Failed to send file!", show_alert=True)

@StreamBot.on_message(filters.channel & (filters.document | filters.video | filters.photo) & ~filters.forwarded, group=-1)
async def channel_receive_handler(bot, broadcast):
    try:
        log_msg = await broadcast.forward(chat_id=Var.BIN_CHANNEL)
        stream_link = f"{Var.URL}watch/{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        online_link = f"{Var.URL}{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

        try:
            await bot.edit_message_reply_markup(
                chat_id=broadcast.chat.id,
                message_id=broadcast.id,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📺 Stream", url=stream_link),
                     InlineKeyboardButton("📥 Download", url=online_link)],
                    [InlineKeyboardButton("📂 Get File", callback_data=f"get_file_{log_msg.id}")],
                    [InlineKeyboardButton("🔗 Share File", callback_data=f"share_file_{log_msg.id}")]
                ])
            )
        except MessageNotModified:
            pass

    except FloodWait as e:
        print(f"Sleeping for {e.x} seconds due to FloodWait.")
        await asyncio.sleep(e.x)
    except Exception as e:
        await bot.send_message(Var.BIN_CHANNEL, f"**Error:** `{e}`")
