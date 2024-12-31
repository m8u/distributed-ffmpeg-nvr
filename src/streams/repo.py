from datetime import datetime
import json
import redis.asyncio as redis

from src.core.singleton import Singleton
from src.settings import Settings

KEY_PREFIX = "ffnvr"


class StreamsRepo(metaclass=Singleton):
    def __init__(self):
        settings = Settings()
        self.redis = redis.from_url(settings.REDIS_DSN)

    async def add(self, guid: str, name: str, url: str) -> None:
        await self.redis.set(f"{KEY_PREFIX}-stream-{guid}", json.dumps({"name": name, "url": url}))

    async def delete(self, guid: str) -> None:
        await self.redis.delete(f"{KEY_PREFIX}-stream-{guid}")

    async def occupy_for(self, guid: str, seconds: int) -> None:
        await self.redis.set(f"{KEY_PREFIX}-stream-{guid}", datetime.now().isoformat()) # ну там чет там да все я спать
