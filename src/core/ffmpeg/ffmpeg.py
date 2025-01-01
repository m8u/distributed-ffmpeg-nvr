import asyncio
from datetime import timedelta
import logging
import os

from src.core.ffmpeg.exceptions import FFmpegError

logger = logging.getLogger()

RTSP_TIMEOUT_SECONDS = 5
RTSP_TIMEOUT_MICROSEC = int(RTSP_TIMEOUT_SECONDS * 1e6)


class FFmpeg:
    def __init__(self):
        self.p = None

    async def record(self, stream_url: str, output_dir: str, segment_time: timedelta) -> None:
        if self.p is not None:
            raise RuntimeError("ffmpeg process is already running")

        os.makedirs(output_dir, exist_ok=True)

        self.p = await asyncio.create_subprocess_shell(
            f"ffmpeg -y -hide_banner -loglevel error"
            f" -rtsp_transport tcp -use_wallclock_as_timestamps 1 -timeout {RTSP_TIMEOUT_MICROSEC}"
            f" -i {stream_url} -c copy -map 0"
            f" -f segment -segment_time {segment_time} -reset_timestamps 1 -segment_atclocktime 1"
            f" -strftime 1 {output_dir}/%Y-%m-%d_%H-%M-%S.mp4"
        )
        logger.debug(
            (
                f"ffmpeg -y -hide_banner -loglevel error"
                f" -rtsp_transport tcp -use_wallclock_as_timestamps 1 -timeout {RTSP_TIMEOUT_MICROSEC}"
                f" -i {stream_url} -c copy -map 0"
                f" -f segment -segment_time {segment_time} -reset_timestamps 1 -segment_atclocktime 1"
                f" -strftime 1 {output_dir}/%Y-%m-%d_%H-%M-%S.mp4"
            )
        )

        while self.p.returncode is None:
            await asyncio.sleep(1)

        return_code = self.p.returncode
        self.p = None

        logger.debug(f"ffmpeg returned {return_code}")
        if return_code != 255:
            raise FFmpegError(f"ffmpeg exited with code {return_code}")

    def stop(self):
        if self.p is None:
            logger.warning("no ffmpeg process bound")
            return
        self.p.terminate()
