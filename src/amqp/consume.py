import asyncio
import logging
import aio_pika

from src.amqp.handle import handle
from src.settings import Settings

logger = logging.getLogger(__name__)


async def consume() -> None:
    settings = Settings()

    connection = await aio_pika.connect_robust(settings.AMQP_DSN)

    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        settings.AMQP_EXCHANGE_NAME, type=aio_pika.ExchangeType.FANOUT, durable=True
    )
    queue = await channel.declare_queue("ffnvr", durable=True)
    await queue.bind(exchange.name, routing_key="")

    async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process():
            logger.debug(message.body)
            await handle(message.body)
            await message.ack()

    await queue.consume(process_message)

    try:
        await asyncio.Future()
    finally:
        await connection.close()
