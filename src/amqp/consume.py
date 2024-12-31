import asyncio
import logging
from typing import Any, Awaitable, Callable
import aio_pika

logger = logging.getLogger(__name__)


async def consume(amqp_dsn: str, exchange_name: str, callback: Callable[[bytes], Awaitable[Any]]):
    connection = await aio_pika.connect_robust(amqp_dsn)

    channel = await connection.channel()

    exchange = await channel.declare_exchange(exchange_name, type=aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("ffnvr", durable=True)
    await queue.bind(exchange.name, routing_key="")

    async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process():
            logger.debug(message.body)
            await callback(message.body)

    await queue.consume(process_message)

    try:
        await asyncio.Future()
    finally:
        await connection.close()
