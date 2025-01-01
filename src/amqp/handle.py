import json
import logging
from src.streams.repo import StreamsRepo

logger = logging.getLogger(__name__)


# {"action": "ADD", "guid": "jopa", "url": "rtsp://kek", "device_name": "jopa жопа jopa"}
async def handle(payload: bytes) -> None:
    streams_repo = StreamsRepo()

    msg: dict = json.loads(payload)
    match msg.pop("action"):
        case "ADD":
            logger.debug("ADD")
            await streams_repo.add(guid=msg["guid"], name=msg["device_name"], url=msg["url"])
        case "DELETE":
            logger.debug("DELETE")
            await streams_repo.delete(guid=msg["guid"])
