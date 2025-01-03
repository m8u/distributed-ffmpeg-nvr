import json
import logging
from src.streams.repo import Stream, StreamsRepo

logger = logging.getLogger(__name__)


async def handle(payload: bytes) -> None:
    streams_repo = StreamsRepo()

    msg: dict = json.loads(payload)
    match msg.pop("action"):
        case "ADD":
            logger.debug("ADD")
            await streams_repo.add(Stream(guid=msg["guid"], url=msg["url"], name=msg["device_name"]))
        case "DELETE":
            logger.debug("DELETE")
            await streams_repo.delete(guid=msg["guid"])
