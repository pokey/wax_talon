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
recording_start_time: float
screenshots: dict


@mod.action_class
class Actions:
    def wax_take_screenshot(name: str):
        """Captures the screen, either as a timestamp in video or to a file, depending on setting.  Name will determine key given to screenshot in log file"""
        screenshot_info = take_screenshot(screenshots_directory, recording_start_time)

        screenshots[name] = screenshot_info

    def x_wax_init_screenshots(
        recording_context: RecordingContext, recording_start_time_: float
    ):
        """
        Initialize screenshot code

        Args:
            recording_context (RecordingContext): Context object with information about recording
            recording_start_time_ (float): The start time of the recording as returned by perfcounter
        """
        global recording_start_time
        global screenshots_directory

        recording_start_time = recording_start_time_

        screenshots_directory = (
            recording_context.recording_log_directory / "screenshots"
        )
        screenshots_directory.mkdir(parents=True)

    def x_wax_reset_screenshots_object():
        """Removes all screenshots from the screenshot object"""
        global screenshots

        screenshots = {}

    def x_wax_get_screenshots_object() -> dict:
        """Gets the screenshot object containing screenshots taken since last reset"""
        return screenshots


def take_screenshot(directory: Path, start_time: float):
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
