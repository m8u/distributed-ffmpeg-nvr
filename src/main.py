import asyncio
import json
import logging
import src.amqp as amqp
from src.streams.repo import StreamsRepo
from src.settings import Settings

logger = logging.getLogger(__name__)


# {"action": "ADD", "guid": "jopa", "url": "rtsp://kek", "device_name": "jopa жопа jopa"}
async def process_amqp_message(payload: bytes) -> None:
    streams_repo = StreamsRepo()

    msg: dict = json.loads(payload)
    match msg.pop("action"):
        case "ADD":
            logger.debug("ADD")
            await streams_repo.add(guid=msg["guid"], name=msg["device_name"], url=msg["url"])
        case "DELETE":
            logger.debug("DELETE")
            await streams_repo.delete(guid=msg["guid"])


async def main():
    settings = Settings()
    logging.basicConfig(level=settings.LOGGING_LEVEL)

    consumer_task = asyncio.create_task(
        amqp.consume(settings.AMQP_DSN, settings.AMQP_EXCHANGE_NAME, process_amqp_message)
    )

    await asyncio.gather(consumer_task)


if __name__ == "__main__":
    asyncio.run(main())

"""
    todo
    1) запушить девайс интегрейшнс
    2) запушить го2ртц
"""
