import asyncio
import logging
import src.amqp as amqp
from src.streams import recordings
from src.settings import Settings

logger = logging.getLogger(__name__)


async def main():
    settings = Settings()
    logging.basicConfig(level=settings.LOGGING_LEVEL)

    amqp_task = asyncio.create_task(amqp.consume())
    recordings_task = asyncio.create_task(recordings.manage())

    await asyncio.gather(amqp_task, recordings_task)


if __name__ == "__main__":
    asyncio.run(main())

"""
    todo
    1) запушить девайс интегрейшнс
    2) запушить го2ртц
"""
