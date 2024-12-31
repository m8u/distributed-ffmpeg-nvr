import asyncio
from datetime import timedelta
import os

from src.core.ffmpeg.ffmpeg import FFmpeg


async def test_record_basic():
    ffmpeg = FFmpeg()

    stream_url = os.getenv("FFNVR_TEST_STREAM")
    os.makedirs("/tmp/ffnvr", exist_ok=True)

    task = asyncio.create_task(ffmpeg.record(stream_url, "/tmp/ffnvr", timedelta(seconds=2)))
    await asyncio.sleep(7)

    ffmpeg.stop()
    await asyncio.gather(task)


async def test_record_wait_loop():
    ffmpeg = FFmpeg()

    stream_url = os.getenv("FFNVR_TEST_STREAM")
    os.makedirs("/tmp/ffnvr", exist_ok=True)

    task = asyncio.create_task(ffmpeg.record(stream_url, "/tmp/ffnvr", timedelta(seconds=2)))

    for _ in range(5):
        done, pending = await asyncio.wait((task,), timeout=0.1)
        assert not done and pending
        await asyncio.sleep(1)

    ffmpeg.stop()

    for _ in range(5):
        done, pending = await asyncio.wait((task,), timeout=0.1)
        if done:
            break
        await asyncio.sleep(1)

    assert done and not pending
    assert done.pop().exception() is None
