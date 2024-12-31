import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from src.core.ffmpeg.ffmpeg import RTSP_TIMEOUT_SECONDS, FFmpeg
from src.streams.repo import StreamsRepo
from src.settings import Settings
from src.streams.utils import get_reconnection_interval


@dataclass
class Recording:
    stream_url: str
    output_dir: str
    ffmpeg: FFmpeg
    task: asyncio.Task
    is_healthy: bool = False
    last_restart: datetime | None = None
    num_restarts: int = 0


async def manage() -> None:
    settings = Settings()
    streams_repo = StreamsRepo()

    recordings: dict[str, Recording] = {}

    while True:
        # check if any streams were deleted and no longer are subjects to record
        streams = await streams_repo.get_all()
        recordings_to_stop = {guid for guid in recordings} - {stream["guid"] for stream in streams}
        for guid in recordings_to_stop:
            recordings[guid].ffmpeg.stop()
            recordings.pop(guid)

        # extend occupation
        for guid in recordings:
            await streams_repo.occupy_for(guid, settings.STREAM_OCCUPATION_TIME)

        # check tasks for exceptions
        done, _ = await asyncio.wait((r.task for r in recordings.values()), timeout=0.1)
        for task in done:
            if task.exception() is None:
                continue
            # todo raise if it's not a timeout or disconnection
            guid = task.get_name()
            recordings[guid].is_healthy = False

        # restart unhealthy ones
        for guid, recording in recordings.items():
            if recording.is_healthy:
                continue
            interval = get_reconnection_interval(recording.num_restarts)
            if recording.last_restart + timedelta(seconds=RTSP_TIMEOUT_SECONDS) + interval < datetime.now():
                # if running, mark as healthy and skip
                if not recording.task.done():
                    recording.is_healthy = True
                    continue
                recording.task = asyncio.create_task(
                    recording.ffmpeg.record(recording.stream_url, recording.output_dir, settings.SEGMENT_TIME),
                    name=guid,
                )

        # if streams quota is not met, check for unoccupied streams
        if len(recordings) < settings.STREAMS_PER_REPLICA and (stream := streams_repo.get_one()):
            # occupy and start recording
            await streams_repo.occupy_for(stream["guid"], settings.STREAM_OCCUPATION_TIME)
            ffmpeg = FFmpeg()
            task = asyncio.create_task(
                ffmpeg.record(stream["url"], stream["name"], settings.SEGMENT_TIME),
                name=stream["guid"],  # stream guid as task name for later identification
            )
            recordings[stream["guid"]] = Recording(stream["url"], stream["name"], ffmpeg, task)

        await asyncio.sleep(1)
