import logging
import mimetypes
import re
import time
from urllib.parse import quote

from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine

from biisal import StartTime, __version__
from biisal.bot import multi_clients, work_loads, StreamBot
from biisal.server.exceptions import FIleNotFound, InvalidHash
from biisal.utils.custom_dl import ByteStreamer
from biisal.utils.render_template import render_page
from biisal.utils.time_format import get_readable_time
from biisal.vars import Var

routes = web.RouteTableDef()
CHUNK_SIZE = 1024 * 1024


@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.json_response({
        "server_status": "running",
        "uptime": get_readable_time(time.time() - StartTime),
        "telegram_bot": "@" + StreamBot.username,
        "connected_bots": len(multi_clients),
        "loads": {
            "bot{}".format(i + 1): load
            for i, (_, load) in enumerate(
                sorted(work_loads.items(), key=lambda item: item[1], reverse=True)
            )
        },
        "version": __version__,
    })


def _extract_message_and_hash(path: str, query_hash: str):
    match = re.fullmatch(r"([a-zA-Z0-9_-]{6})(\d+)", path)
    if match:
        return int(match.group(2)), match.group(1)
    match = re.search(r"(\d+)(?:/\S+)?", path)
    if not match:
        raise web.HTTPBadRequest(text="Invalid file URL")
    return int(match.group(1)), query_hash


def _parse_byte_range(header, file_size):
    if not header:
        return 0, file_size - 1, False
    if file_size <= 0 or not header.startswith("bytes=") or "," in header:
        raise ValueError("Invalid byte range")
    value = header[6:].strip()
    if "-" not in value:
        raise ValueError("Invalid byte range")
    start_text, end_text = value.split("-", 1)
    if not start_text:
        suffix = int(end_text)
        if suffix <= 0:
            raise ValueError("Invalid suffix range")
        start = max(file_size - suffix, 0)
        end = file_size - 1
    else:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1
    if start < 0 or start >= file_size or end < start:
        raise ValueError("Unsatisfiable byte range")
    return start, min(end, file_size - 1), True


@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_route_handler(request: web.Request):
    try:
        message_id, secure_hash = _extract_message_and_hash(
            request.match_info["path"], request.rel_url.query.get("hash", "")
        )
        return web.Response(
            text=await render_page(message_id, secure_hash),
            content_type="text/html",
        )
    except InvalidHash as exc:
        raise web.HTTPForbidden(text=exc.message)
    except FIleNotFound as exc:
        raise web.HTTPNotFound(text=exc.message)
    except (ConnectionResetError, BrokenPipeError, BadStatusLine):
        raise web.HTTPBadRequest(text="Client disconnected")
    except web.HTTPException:
        raise
    except Exception:
        logging.exception("Failed to render stream page")
        raise web.HTTPInternalServerError(text="Unable to render file page")


@routes.get(r"/{path:\S+}", allow_head=True)
async def download_route_handler(request: web.Request):
    try:
        message_id, secure_hash = _extract_message_and_hash(
            request.match_info["path"], request.rel_url.query.get("hash", "")
        )
        return await media_streamer(request, message_id, secure_hash)
    except InvalidHash as exc:
        raise web.HTTPForbidden(text=exc.message)
    except FIleNotFound as exc:
        raise web.HTTPNotFound(text=exc.message)
    except (ConnectionResetError, BrokenPipeError, BadStatusLine):
        # A browser/download manager closing the connection is not a server fault.
        raise web.HTTPBadRequest(text="Client disconnected")
    except web.HTTPException:
        raise
    except Exception:
        logging.exception("Media streaming failed")
        raise web.HTTPInternalServerError(text="Unable to stream this file")


class_cache = {}


async def media_streamer(request: web.Request, message_id: int, secure_hash: str):
    if not multi_clients or not work_loads:
        raise web.HTTPServiceUnavailable(text="Telegram clients are not ready")

    client_index = min(work_loads, key=work_loads.get)
    client = multi_clients.get(client_index)
    if client is None:
        raise web.HTTPServiceUnavailable(text="No Telegram client is available")

    if client not in class_cache:
        class_cache[client] = ByteStreamer(client)
    streamer = class_cache[client]

    file_id = await streamer.get_file_properties(message_id)
    if not secure_hash or file_id.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = int(file_id.file_size or 0)
    if file_size <= 0:
        raise FIleNotFound

    try:
        start, end, is_partial = _parse_byte_range(
            request.headers.get("Range"), file_size
        )
    except (ValueError, TypeError):
        return web.Response(
            status=416,
            text="416: Range not satisfiable",
            headers={"Content-Range": "bytes */{}".format(file_size)},
        )

    offset = start - (start % CHUNK_SIZE)
    first_part_cut = start - offset
    last_part_cut = (end % CHUNK_SIZE) + 1
    part_count = ((end - offset) // CHUNK_SIZE) + 1

    body = streamer.yield_file(
        file_id,
        client_index,
        offset,
        first_part_cut,
        last_part_cut,
        part_count,
        CHUNK_SIZE,
    )

    mime_type = file_id.mime_type or ""
    file_name = file_id.file_name or "download"
    if not mime_type:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    safe_name = file_name.replace("\r", "").replace("\n", "").replace('"', "'")
    headers = {
        "Content-Type": mime_type,
        "Content-Length": str(end - start + 1),
        "Content-Disposition": "attachment; filename*=UTF-8''{}".format(quote(safe_name)),
        "Accept-Ranges": "bytes",
    }
    if is_partial:
        headers["Content-Range"] = "bytes {}-{}/{}".format(start, end, file_size)

    return web.Response(status=206 if is_partial else 200, body=body, headers=headers)
