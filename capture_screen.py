import time
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

screenshots_directory: Path
recording_context: RecordingContext
recording_start_time: float
screenshots: dict


@mod.action_class
class Actions:
    def wax_capture_screen(name: str):
        """Captures the screen, either as a timestamp in video or to a file, depending on setting.  Name will determine key given to screenshot in log file"""
        screenshot_info = capture_screen(screenshots_directory, recording_start_time)

        screenshots[name] = screenshot_info

    def _wax_init_capture_screen(
        _recording_context: RecordingContext, _recording_start_time: float
    ):
        global recording_context
        global recording_start_time

        recording_context = _recording_context
        recording_start_time = _recording_start_time

        screenshots_directory = (
            recording_context.recording_log_directory / "screenshots"
        )
        screenshots_directory.mkdir(parents=True)

    def _wax_reset_screenshots_object():
        global screenshots

        screenshots = {}

    def _wax_get_screenshots_object() -> dict:
        return screenshots


def capture_screen(directory: Path, start_time: float):
    timestamp = time.perf_counter() - start_time

    if screenshot_time_stamp_only.get():
        filename = None
    else:
        img = screen.capture_rect(screen.main_screen().rect)
        date = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S-%f")
        filename = f"{date}.png"
        path = directory / filename
        # NB: Writing the image to the file is expensive so we do it asynchronously
        cron.after("50ms", lambda: img.write_file(path))

    return {
        "filename": filename,
        "timeOffset": timestamp,
    }
