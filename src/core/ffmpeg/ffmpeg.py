import asyncio
from asyncio.subprocess import PIPE
from contextlib import suppress
from datetime import datetime, timedelta
import logging
import os

from src.core.ffmpeg.exceptions import FFmpegError

logger = logging.getLogger()

RTSP_TIMEOUT_SECONDS = 5
RTSP_TIMEOUT_MICROSEC = int(RTSP_TIMEOUT_SECONDS * 1e6)
TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"


class FFmpeg:
    def __init__(self):
        self.p = None

    async def record(self, stream_url: str, output_dir: str, segment_time: timedelta, num_segments: int) -> None:
        """
        Starts ffmpeg process and waits for it to exit. Raises FFmpegError for all exit codes except when stopped with stop()
        """
        if self.p is not None:
            raise RuntimeError("ffmpeg process is already running")

        self.output_dir = output_dir
        self.segment_time = segment_time
        self.num_segments = num_segments

        os.makedirs(output_dir, exist_ok=True)

        self.p = await asyncio.create_subprocess_shell(
            f"ffmpeg -y -hide_banner -loglevel error"
            f" -rtsp_transport tcp -use_wallclock_as_timestamps 1 -timeout {RTSP_TIMEOUT_MICROSEC}"
            f" -i {stream_url} -c:v copy -map 0"
            f" -f segment -segment_time {segment_time} -reset_timestamps 1 -segment_atclocktime 1"
            f" -strftime 1 '{output_dir}/.{TIMESTAMP_FORMAT}.mp4'"
        )

        while self.p.returncode is None:
            await asyncio.sleep(1)
            await asyncio.gather(self._rename_segments(), self._remove_segments())

        return_code = self.p.returncode
        self.p = None

        logger.debug(f"ffmpeg returned {return_code}")
        if return_code != 255:
            raise FFmpegError(f"ffmpeg exited with code {return_code}")

    def stop(self):
        """
        Terminates ffmpeg process
        """
        if self.p is None:
            logger.warning("no ffmpeg process bound")
            return
        self.p.terminate()

    async def _rename_segments(self) -> None:
        """
        Renames segment files to remove dot prefix & add end timestamps
        """
        segments = os.listdir(self.output_dir)
        for filename in segments:
            if not filename.startswith("."):
                continue
            p = await asyncio.create_subprocess_shell(f"lsof | grep ffmpeg | grep {filename}", stdout=PIPE, stderr=PIPE)
            if await p.wait() == 0:
                # segment is being written, skip
                continue

            p = await asyncio.create_subprocess_shell(
                f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{self.output_dir}/{filename}'",
                stdout=PIPE,
                stderr=PIPE,
            )
            result, _ = await p.communicate()
            if p.returncode != 0:
                # there can be broken segments (due to crashes etc.), so let's just remove them ¯\_(ツ)_/¯
                logger.warning(f"ffprobe returned {p.returncode}, removing {self.output_dir}/{filename}")
                with suppress(FileNotFoundError):
                    os.remove(f"{self.output_dir}/{filename}")
                continue

            duration_seconds = float(result.decode())
            start_ts = datetime.strptime(filename.removeprefix(".").removesuffix(".mp4"), TIMESTAMP_FORMAT)
            end_ts = start_ts + timedelta(seconds=duration_seconds)

            new_filename = f"{start_ts.strftime(TIMESTAMP_FORMAT)}_{end_ts.strftime(TIMESTAMP_FORMAT)}.mp4"
            os.rename(f"{self.output_dir}/{filename}", f"{self.output_dir}/{new_filename}")

    async def _remove_segments(self) -> None:
        """
        Removes segment files older than SEGMENT_TIME * NUM_SEGMENTS
        """
        mtime_days = self.segment_time.total_seconds() / (60 * 60 * 24) * (self.num_segments + 1)
        p = await asyncio.create_subprocess_shell(f"find '{self.output_dir}' -type f -mtime {mtime_days} -delete")
        await p.wait()
