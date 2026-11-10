import logging
import urllib.parse
from pathlib import Path

import jinja2

from biisal.vars import Var
from biisal.utils.human_readable import humanbytes
from biisal.utils.file_properties import get_file_ids
from biisal.server.exceptions import FIleNotFound


_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template"
_TEMPLATE_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=jinja2.select_autoescape(("html", "xml")),
)


async def render_page(message_id, secure_hash, src=None):
    file_data = await get_file_ids(
        # The BIN channel is the authoritative source for streamed files.
        __import__("biisal.bot", fromlist=["StreamBot"]).StreamBot,
        int(Var.BIN_CHANNEL),
        int(message_id),
    )

    actual_hash = (file_data.unique_id or "")[:6]
    if not secure_hash or actual_hash != secure_hash:
        logging.debug(
            "Invalid hash for message %s: requested=%s actual=%s",
            message_id, secure_hash, actual_hash,
        )
        from biisal.server.exceptions import InvalidHash
        raise InvalidHash

    file_name = file_data.file_name or "download"
    src = urllib.parse.urljoin(
        Var.URL,
        f"{message_id}/{urllib.parse.quote_plus(file_name)}?hash={actual_hash}",
    )

    mime_type = file_data.mime_type or "application/octet-stream"
    media_type = mime_type.split("/", 1)[0].lower()
    template_name = "req.html" if media_type in {"video", "audio"} else "dl.html"

    template = _TEMPLATE_ENV.get_template(template_name)
    return template.render(
        file_name=file_name.replace("_", " "),
        file_url=src,
        file_size=humanbytes(int(file_data.file_size or 0)),
        file_unique_id=file_data.unique_id or "",
    )
