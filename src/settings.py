from datetime import timedelta
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOGGING_LEVEL: str

    AMQP_DSN: str
    AMQP_EXCHANGE_NAME: str

    REDIS_DSN: str

    STREAMS_PER_REPLICA: int = 8
    STREAM_OCCUPATION_TIME: int = 10
    RECORDINGS_MOUNT_POINT: str
    SEGMENT_TIME: timedelta
