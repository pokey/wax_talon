import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from talon import Module, cron, screen

from .types import RecordingContext

mod = Module()

screenshot_time_stamp_only = mod.setting(
    "wax_screenshot_time_stamp_only",
    type=bool,
    default=True,
    desc="If `True`, don't actually take a screenshot during recording just capture the timestamp so that we can extract it from the video later",
)


class Screenshots:
    screenshots_directory: Path
    recording_start_time: float
    screenshots: dict

    def init(self, recording_context: RecordingContext, recording_start_time: float):
        """
        Initialize screenshot code

        Args:
            recording_context (RecordingContext): Context object with information about recording
            recording_start_time_ (float): The start time of the recording as returned by perfcounter
        """

        self.recording_start_time = recording_start_time

        self.screenshots_directory = (
            recording_context.recording_log_directory / "screenshots"
        )
        self.screenshots_directory.mkdir(parents=True)

        self.screenshots = {}

    @contextmanager
    def init_object(self):
        self.screenshots = {}
        yield self.screenshots

    def take_screenshot(self, name: str):
        """Captures the screen, either as a timestamp in video or to a file, depending on setting.  Name will determine key given to screenshot in log file"""
        timestamp = time.perf_counter() - self.recording_start_time

        if screenshot_time_stamp_only.get():
            filename = None
        else:
            img = screen.capture_rect(screen.main_screen().rect)
            date = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S-%f")
            filename = f"{date}.png"
            path = self.screenshots_directory / filename
            # NB: Writing the image to the file is expensive so we do it asynchronously
            cron.after("50ms", lambda: img.write_file(path))

        self.screenshots[name] = {
            "filename": filename,
            "timeOffset": timestamp,
        }


screenshots = Screenshots()


@mod.action_class
class User:
    def wax_take_screenshot(name: str):
        """Captures the screen, either as a timestamp in video or to a file, depending on setting.  Name will determine key given to screenshot in log file"""
        screenshots.take_screenshot(name)
