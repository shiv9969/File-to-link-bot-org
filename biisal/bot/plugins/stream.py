import asyncio
import logging
import os
from urllib.parse import quote_plus

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from biisal.bot import StreamBot
from biisal.utils.database import Database
from biisal.utils.file_properties import (
    get_hash,
    get_media_file_size,
    get_name,
)
from biisal.utils.human_readable import humanbytes
from biisal.vars import Var

logger = logging.getLogger(__name__)
db = Database(Var.DATABASE_URL, Var.name)

MY_PASS = os.environ.get("MY_PASS")
pass_dict = {}
pass_db = Database(Var.DATABASE_URL, "ag_passwords")

MESSAGE_TEXT = (
    "<b>‣ ʏᴏᴜʀ ʟɪɴᴋ ɢᴇɴᴇʀᴀᴛᴇᴅ ! 😎\n\n"
    "‣ Fɪʟᴇ ɴᴀᴍᴇ : <i>{}</i>\n"
    "‣ Fɪʟᴇ ꜱɪᴢᴇ : {}\n\n"
    "‣ ❤️ Powered By : @BoB_Files1✨🫶</b>"
)


async def _notify_bin(text: str) -> None:
    try:
        await StreamBot.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=text,
            disable_web_page_preview=True,
        )
    except Exception:
        logger.exception("Unable to send a diagnostic message to BIN_CHANNEL")


def _make_link(message: Message) -> tuple[str, str]:
    message_id = str(message.id)
    name = quote_plus(get_name(message))
    file_hash = get_hash(message)
    if not file_hash:
        raise ValueError("The forwarded message does not contain supported media")
    stream_url = f"{Var.URL}watch/{message_id}/{name}?hash={file_hash}"
    download_url = f"{Var.URL}{message_id}/{name}?hash={file_hash}"
    return stream_url, download_url


async def _forward_with_flood_wait(message: Message) -> Message:
    while True:
        try:
            return await message.forward(chat_id=Var.BIN_CHANNEL)
        except FloodWait as exc:
            wait_seconds = int(getattr(exc, "value", getattr(exc, "x", 1)))
            logger.warning("Telegram FloodWait: sleeping for %s seconds", wait_seconds)
            await asyncio.sleep(max(1, wait_seconds))


@StreamBot.on_message(
    filters.private
    & (filters.document | filters.video | filters.audio | filters.photo),
    group=4,
)
async def private_receive_handler(client: Client, message: Message):
    if not message.from_user:
        return

    try:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id)
            await _notify_bin(
                "New user started the bot: "
                f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            )
    except Exception:
        # Database/logging failure should not prevent a user from getting a file link.
        logger.exception("Unable to update new-user database record")

    if Var.UPDATES_CHANNEL and Var.UPDATES_CHANNEL != "None":
        try:
            member = await client.get_chat_member(Var.UPDATES_CHANNEL, message.from_user.id)
            if getattr(member, "status", None) == "kicked":
                await message.reply_text(
                    "You are banned. Contact support: https://t.me/assaulter_shiv"
                )
                return
        except UserNotParticipant:
            await message.reply_text(
                "Please join our updates channel to use this bot.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(
                        "Join updates channel",
                        url=f"https://t.me/{Var.UPDATES_CHANNEL.lstrip('@')}",
                    )]]
                ),
            )
            return
        except Exception:
            logger.exception("Updates-channel membership check failed")
            await message.reply_text(
                "I couldn't verify your channel membership. Please try again later."
            )
            return

    try:
        log_message = await _forward_with_flood_wait(message)
        stream_url, download_url = _make_link(log_message)

        await log_message.reply_text(
            text=(
                f"**Requested by:** [{message.from_user.first_name}]"
                f"(tg://user?id={message.from_user.id})\n"
                f"**User ID:** `{message.from_user.id}`\n"
                f"**Stream link:** {stream_url}"
            ),
            disable_web_page_preview=True,
            quote=True,
        )
        await message.reply_text(
            text=MESSAGE_TEXT.format(
                get_name(log_message) or "File",
                humanbytes(get_media_file_size(log_message)),
            ),
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("STREAM", url=stream_url),
                    InlineKeyboardButton("DOWNLOAD", url=download_url),
                ]]
            ),
        )
    except Exception:
        logger.exception("Failed to process private media message %s", message.id)
        await message.reply_text(
            "Sorry, I couldn't create a link for this file. Please try again."
        )


@StreamBot.on_message(
    filters.channel
    & (filters.document | filters.video | filters.audio | filters.photo)
    & ~filters.forwarded,
    group=-1,
)
async def channel_receive_handler(client: Client, broadcast: Message):
    channel_id = int(broadcast.chat.id)

    if channel_id in Var.BAN_CHNL:
        logger.info("Skipping link generation for configured BAN_CHNL channel %s", channel_id)
        return

    if channel_id in Var.BANNED_CHANNELS:
        logger.info("Leaving explicitly configured banned channel %s", channel_id)
        try:
            await client.leave_chat(channel_id)
        except Exception:
            logger.exception("Unable to leave configured banned channel %s", channel_id)
        return

    try:
        log_message = await _forward_with_flood_wait(broadcast)
        stream_url, download_url = _make_link(log_message)

        await log_message.reply_text(
            text=(
                f"**Channel:** `{broadcast.chat.title or channel_id}`\n"
                f"**Channel ID:** `{channel_id}`\n"
                f"**Stream URL:** {stream_url}"
            ),
            quote=True,
            disable_web_page_preview=True,
        )

        try:
            await client.edit_message_reply_markup(
                chat_id=channel_id,
                message_id=broadcast.id,
                reply_markup=InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton("STREAM", url=stream_url),
                        InlineKeyboardButton("DOWNLOAD", url=download_url),
                    ]]
                ),
            )
        except Exception as exc:
            if exc.__class__.__name__ == "MessageNotModified":
                logger.debug("Buttons already match on channel message %s", broadcast.id)
            else:
                raise

    except Exception as exc:
        error_name = exc.__class__.__name__
        if error_name in {"ChatForwardsRestricted", "MessageIdInvalid", "MessageEmpty"}:
            logger.warning(
                "Skipping channel message %s in %s: %s: %s",
                broadcast.id, channel_id, error_name, exc,
            )
            await _notify_bin(
                f"Skipped channel message `{broadcast.id}` in `{channel_id}`: "
                f"`{error_name}`. Check source message availability and channel settings."
            )
            return

        logger.exception(
            "Failed to process channel message %s in %s",
            broadcast.id, channel_id,
        )
        await _notify_bin(
            f"Channel message processing failed. Channel: `{channel_id}`, "
            f"message: `{broadcast.id}`, error: `{error_name}: {exc}`"
        )
