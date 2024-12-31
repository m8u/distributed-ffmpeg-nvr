import asyncio
from datetime import timedelta

from src.core.ffmpeg.exceptions import FFmpegError

RTSP_TIMEOUT_SECONDS = 5
RTSP_TIMEOUT_NANOSEC = RTSP_TIMEOUT_SECONDS * 10e6


class FFmpeg:
    def __init__(self):
        self.p = None

    async def record(self, stream_url: str, output_dir: str, segment_time: timedelta) -> None:
        if self.p is not None:
            raise RuntimeError("ffmpeg process is already running")

        self.p = await asyncio.create_subprocess_shell(
            f"ffmpeg -y -rtsp_transport tcp -use_wallclock_as_timestamps 1 -timeout {RTSP_TIMEOUT_NANOSEC}"
            f" -i {stream_url} -c copy -map 0"
            f" -f segment -segment_time {segment_time} -reset_timestamps 1 -segment_atclocktime 1"
            f" -strftime 1 {output_dir}/%Y-%m-%d_%H-%M-%S.mp4"
        )

        while self.p.returncode is None:
            await asyncio.sleep(1)

        print(f"(debug) ffmpeg returned {self.p.returncode}")
        if self.p.returncode != 255:
            self.p = None
            raise FFmpegError(f"ffmpeg exited with code {self.p.returncode}")

    def stop(self):
        if self.p is None:
            raise RuntimeError("no ffmpeg process bound")

        self.p.terminate()
        self.p = None
