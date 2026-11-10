from typing import Any, Optional

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.file_id import FileId

from biisal.server.exceptions import FIleNotFound


def get_media_from_message(message: Optional[Message]) -> Any:
    if message is None or getattr(message, "empty", False):
        return None
    for attr in (
        "audio", "document", "photo", "sticker", "animation",
        "video", "voice", "video_note",
    ):
        media = getattr(message, attr, None)
        if media:
            return media
    return None


async def parse_file_id(message: Message) -> Optional[FileId]:
    media = get_media_from_message(message)
    if media is None:
        return None
    return FileId.decode(media.file_id)


async def parse_file_unique_id(message: Message) -> Optional[str]:
    media = get_media_from_message(message)
    return media.file_unique_id if media is not None else None


async def get_file_ids(client: Client, chat_id: int, id: int) -> Optional[FileId]:
    try:
        message = await client.get_messages(chat_id, id)
    except Exception as exc:
        if exc.__class__.__name__ in {"MessageIdInvalid", "MessageEmpty", "PeerIdInvalid"}:
            raise FIleNotFound from exc
        raise

    if message is None or getattr(message, "empty", False):
        raise FIleNotFound

    media = get_media_from_message(message)
    if media is None:
        raise FIleNotFound

    file_id = FileId.decode(media.file_id)
    if file_id is None:
        raise FIleNotFound

    file_id.file_size = getattr(media, "file_size", 0) or 0
    file_id.mime_type = getattr(media, "mime_type", "") or ""
    file_id.file_name = getattr(media, "file_name", "") or ""
    file_id.unique_id = getattr(media, "file_unique_id", "") or ""
    return file_id


def get_hash(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6] if media else ""


def get_name(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_name", "") or "file" if media else "file"


def get_media_file_size(message: Message) -> int:
    media = get_media_from_message(message)
    return getattr(media, "file_size", 0) or 0 if media else 0
