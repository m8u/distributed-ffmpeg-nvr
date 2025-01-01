import asyncio
from dataclasses import dataclass
import logging
import random
from uuid import uuid4
import json
import redis.asyncio as redis

from src.core.singleton import Singleton
from src.settings import Settings

logger = logging.getLogger(__name__)

KEY_PREFIX = "ffnvr"


@dataclass
class Stream:
    guid: str
    url: str
    name: str


class StreamsRepo(metaclass=Singleton):
    def __init__(self):
        self.settings = Settings()
        self._redis = redis.from_url(self.settings.REDIS_DSN)
        self._uuid = uuid4()

    async def add(self, stream: Stream) -> None:
        await self._redis.set(
            f"{KEY_PREFIX}-stream-{stream.guid}",
            json.dumps({"guid": stream.guid, "name": stream.name, "url": stream.url}),
        )

    async def delete(self, guid: str) -> None:
        await self._redis.delete(f"{KEY_PREFIX}-stream-{guid}")

    async def get_all(self) -> list[Stream]:
        keys = await self._redis.keys(f"{KEY_PREFIX}-stream-*")
        streams = []
        for key in keys:
            stream_data = json.loads(await self._redis.get(key))
            streams.append(Stream(guid=stream_data["guid"], name=stream_data["name"], url=stream_data["url"]))
        return streams

    async def occupy(self, seconds: int) -> Stream | None:
        """
        Try to occupy an unoccupied stream, and return it.
        If there are no unoccupied streams, return None.
        """
        while True:
            stream_keys = await self._redis.keys(f"{KEY_PREFIX}-stream-*")
            lock_keys = await self._redis.keys(f"{KEY_PREFIX}-lock-*")
            unoccupied = set(k.decode().removeprefix(f"{KEY_PREFIX}-stream-") for k in stream_keys) - set(
                k.decode().removeprefix(f"{KEY_PREFIX}-lock-") for k in lock_keys
            )
            for guid in unoccupied:
                ok = await self._redis.set(f"{KEY_PREFIX}-lock-{guid}", str(self._uuid), ex=seconds, nx=True)
                logger.debug(f"redis returned {ok} when trying to occupy stream")
                if not ok:
                    await asyncio.sleep(random.random())
                    continue
                stream_data = json.loads(await self._redis.get(f"{KEY_PREFIX}-stream-{guid}"))
                return Stream(guid=stream_data["guid"], name=stream_data["name"], url=stream_data["url"])

            return None

    async def extend(self, guid: str, seconds: int) -> None:
        await self._redis.set(f"{KEY_PREFIX}-lock-{guid}", str(self._uuid), ex=seconds, nx=False)
