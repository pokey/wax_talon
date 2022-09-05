from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RecordingContext:
    recording_log_directory: Path


@dataclass
class PhraseInfo:
    phrase_id: str
    parsed: list[list[Any]]


class Recorder:
    # Set this to true if the given recorder shows a calibration display at the
    # start so that it will be run after all the other recorders have started.
    # In particular this will attempt to ensure that it runs after screen
    # recording has begun so the calibration display makes it into the final
    # recording
    has_calibration_display = False

    def check_can_start(self):
        """
        Checks that the necessary prerequisites are met to begin recording;
        throwing an exception if not.  For example, a particular application
        may need to be running or focused.
        """
        pass

    def check_can_stop(self):
        """
        Checks that the necessary prerequisites are met to stop recording;
        throwing an exception if not.  For example, a particular application
        may need to be running or focused.
        """
        pass

    def start_recording(self, context: RecordingContext):
        """Begins recording for this recorder"""
        pass

    def capture_pre_phrase(self, phrase_info: PhraseInfo):
        """Capture anything you'd like to capture right before every phrase is executed"""
        pass

    def capture_post_phrase(self, phrase_info: PhraseInfo):
        """Capture anything you'd like to capture right after every phrase is executed"""
        pass

    def stop_recording(self):
        """Stops recording for this recorder"""
        pass
