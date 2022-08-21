from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


@dataclass
class RecordingContext:
    recording_log_directory: Path
    screenshots_directory: Path


@dataclass
class PhraseInfo:
    phrase_id: str
    parsed: Iterable[list[Any]]


@dataclass
class ExtraCaptureFields:
    screenshots: dict[str, dict] = {}
    extra_fields: dict = {}


class Recorder(ABC):
    @abstractmethod
    def check_can_start(self):
        """
        Checks that the necessary prerequisites are met to begin recording;
        throwing an exception if not.  For example, a particular application
        may need to be running or focused.
        """
        pass

    @abstractmethod
    def check_can_stop(self):
        """
        Checks that the necessary prerequisites are met to stop recording;
        throwing an exception if not.  For example, a particular application
        may need to be running or focused.
        """
        pass

    @abstractmethod
    def start_recording(self, context: RecordingContext) -> Optional[dict]:
        """Begins recording for this recorder"""
        pass

    @abstractmethod
    def capture_pre_phrase(self) -> Optional[ExtraCaptureFields]:
        """Capture anything you'd like to capture right before every phrase is executed"""
        pass

    @abstractmethod
    def capture_post_phrase(self) -> Optional[ExtraCaptureFields]:
        """Capture anything you'd like to capture right after every phrase is executed"""
        pass

    @abstractmethod
    def stop_recording(self):
        """Stops recording for this recorder"""
        pass
