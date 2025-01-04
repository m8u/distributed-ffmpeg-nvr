import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import os
from src.core.ffmpeg.exceptions import FFmpegError
from src.core.ffmpeg.ffmpeg import RTSP_TIMEOUT_SECONDS, FFmpeg
from src.streams.repo import Stream, StreamsRepo
from src.settings import Settings
from src.streams.utils import get_reconnection_interval

logger = logging.getLogger()


@dataclass
class Recording:
    stream: Stream
    ffmpeg: FFmpeg
    task: asyncio.Task
    output_dir: str
    is_healthy: bool = True
    last_restart: datetime | None = None
    num_restarts: int = 0


async def manage() -> None:
    settings = Settings()
    streams_repo = StreamsRepo()

    os.makedirs(settings.RECORDINGS_MOUNT_POINT, exist_ok=True)

    recordings: dict[str, Recording] = {}

    while True:
        await asyncio.sleep(1)

        # check if any streams were deleted and no longer are subjects to record
        streams = await streams_repo.get_all()
        recordings_to_stop = {guid for guid in recordings} - {stream.guid for stream in streams}
        for guid in recordings_to_stop:
            recordings[guid].ffmpeg.stop()
            await asyncio.gather(recordings[guid].task, return_exceptions=True)
            recordings.pop(guid)

        # extend occupation
        for guid in recordings:
            await streams_repo.extend(guid, settings.STREAM_OCCUPATION_TIME)

        # check tasks for exceptions
        if len(recordings) > 0:
            done, _ = await asyncio.wait((r.task for r in recordings.values()), timeout=0.1)
            for task in done:
                exc = task.exception()
                if exc is None:
                    continue
                if exc is not FFmpegError:
                    raise exc
                guid = task.get_name()
                recordings[guid].is_healthy = False

        # restart unhealthy ones
        for guid, recording in recordings.items():
            if recording.is_healthy:
                continue
            interval = get_reconnection_interval(recording.num_restarts)
            restart_at = (recording.last_restart or datetime.min) + timedelta(seconds=RTSP_TIMEOUT_SECONDS) + interval
            if restart_at < datetime.now():
                # if running, mark as healthy and skip
                if not recording.task.done():
                    recording.is_healthy = True
                    recording.num_restarts = 0
                    continue
                recording.num_restarts += 1
                recording.last_restart = datetime.now()
                recording.task = asyncio.create_task(
                    recording.ffmpeg.record(
                        recording.stream.url, recording.output_dir, settings.SEGMENT_TIME, settings.NUM_SEGMENTS
                    ),
                    name=guid,
                )

        # if streams quota isn't met, check for unoccupied streams
        if len(recordings) < settings.STREAMS_PER_REPLICA:
            stream = await streams_repo.occupy(settings.STREAM_OCCUPATION_TIME)
            if stream is None:
                continue
            logger.info(f"start recording stream {stream.name}")
            ffmpeg = FFmpeg()
            parent_dir = f"{stream.name.split(' (')[0]}/" if " (" in stream.name else ""
            output_dir = f"{settings.RECORDINGS_MOUNT_POINT}/{parent_dir}{stream.name}"
            task = asyncio.create_task(
                ffmpeg.record(stream.url, output_dir, settings.SEGMENT_TIME, settings.NUM_SEGMENTS),
                name=stream.guid,  # stream guid as task name for later identification
            )
            recordings[stream.guid] = Recording(stream, ffmpeg, task, output_dir)
