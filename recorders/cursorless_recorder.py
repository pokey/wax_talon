from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

import yaml
from talon import Context, Module, actions, ui
from talon.ui import UIErr

from ..types import PhraseInfo, Recorder, RecordingContext

mod = Module()
ctx = Context()

recording_screen_vscode_ctx = Context()
recording_screen_vscode_ctx.matches = r"""
tag: user.wax_is_recording
app: vscode
"""

snapshots_directory: Path
recording_context: RecordingContext


@mod.action_class
class Actions:
    def wax_cursorless_recorder(should_take_mark_screenshots: bool = True) -> Recorder:
        """
        Returns an object that can be used for recording cursorless commands.


        Args:
            should_take_mark_screenshots (bool, optional): Whether to highlight
            the marks referenced in a phrase.  Can set this to False if you're
            not recording the screen. Defaults to True.

        Returns:
            Recorder: A recorder that can be passed as an argument to
            `user.wax_start_recording()`
        """
        return CursorlessRecorder(should_take_mark_screenshots)

    def private_wax_cursorless_snapshot(
        path: str, metadata: Any, decorated_marks: list[dict]
    ):
        """Take a Cursorless pre- or post-phrase snapshot"""


@ctx.action_class("user")
class UserActions:
    def private_wax_cursorless_snapshot(
        path: str, metadata: Any, decorated_marks: list[dict]
    ):
        # Turn this one off globally
        pass


class CursorlessRecorder(Recorder):
    has_calibration_display = True

    def __init__(self, should_take_mark_screenshots):
        self.should_take_mark_screenshots = should_take_mark_screenshots

    def check_can_start(self):
        # VSCode needs to be running
        get_vscode_app()

    def check_can_stop(self):
        # VSCode needs to be running
        get_vscode_app()

    def start_recording(self, context: RecordingContext):
        global snapshots_directory
        global recording_context

        # Need VSCode in front
        actions.user.switcher_focus_app(get_vscode_app())

        commands_directory = context.recording_log_directory / "commands"
        commands_directory.mkdir(parents=True)

        snapshots_directory = context.recording_log_directory / "snapshots"
        snapshots_directory.mkdir(parents=True)

        # Start cursorless recording
        command_payload = actions.user.vscode_get(
            "cursorless.recordTestCase",
            {
                "isSilent": True,
                "directory": str(commands_directory),
                "extraSnapshotFields": ["timeOffsetSeconds"],
                "showCalibrationDisplay": True,
            },
        )

        actions.user.wax_log_object(
            {"type": "cursorlessInit", "extensionRecordStartPayload": command_payload}
        )

    def capture_pre_phrase(self, phrase: PhraseInfo):
        decorated_marks = list(extract_decorated_marks(phrase.parsed))

        actions.user.private_wax_cursorless_snapshot(
            str(snapshots_directory / f"{phrase.phrase_id}-prePhrase.yaml"),
            {"phraseId": phrase.phrase_id, "type": "prePhrase"},
            decorated_marks,
        )

        if self.should_take_mark_screenshots:
            take_mark_screenshots(decorated_marks)

    def capture_post_phrase(self, phrase: PhraseInfo):
        actions.user.private_wax_cursorless_snapshot(
            str(snapshots_directory / f"{phrase.phrase_id}-postPhrase.yaml"),
            {"phraseId": phrase.phrase_id, "type": "postPhrase"},
            [],
        )

    def stop_recording(self):
        # Need VSCode in front
        actions.user.switcher_focus_app(get_vscode_app())

        # Stop cursorless recording
        actions.user.vscode("cursorless.recordTestCase")


def take_mark_screenshots(decorated_marks: list[dict]):
    if not decorated_marks:
        return None

    all_decorated_marks_target = actions.user.cursorless_v1_build_list_target(
        [
            actions.user.cursorless_v1_build_primitive_target([], mark)
            for mark in decorated_marks
        ]
    )

    with cursorless_recording_paused():
        actions.user.cursorless_v1_action_highlight(
            all_decorated_marks_target, "highlight1"
        )

        actions.sleep("50ms")

        actions.user.wax_take_screenshot("decoratedMarks.all")

        actions.user.cursorless_v1_action_highlight(
            actions.user.cursorless_v1_target_nothing(), "highlight1"
        )


def extract_decorated_marks(parsed: Iterable[list[Any]]):
    for capture_list in parsed:
        for capture in capture_list:
            items = capture if isinstance(capture, list) else [capture]
            for item in items:
                try:
                    yield from actions.user.cursorless_v1_extract_decorated_marks(item)
                except TypeError:
                    continue


@contextmanager
def cursorless_recording_paused():
    actions.user.vscode("cursorless.pauseRecording")
    yield
    actions.user.vscode("cursorless.resumeRecording")


@recording_screen_vscode_ctx.action_class("user")
class UserActions:
    def private_wax_cursorless_snapshot(
        path: str, metadata: Any, decorated_marks: list[dict]
    ):
        try:
            use_pre_phrase_snapshot = actions.user.did_emit_pre_phrase_signal()
        except KeyError:
            use_pre_phrase_snapshot = False

        try:
            ui.active_window().children.find_one(AXRole="AXMenu", max_depth=0)
            menu_showing = True
        except UIErr:
            menu_showing = False

        if not menu_showing:
            try:
                actions.user.vscode_with_plugin_and_wait(
                    "cursorless.takeSnapshot",
                    path,
                    metadata,
                    decorated_marks,
                    use_pre_phrase_snapshot,
                )
            except Exception as e:
                with open(path, "w") as f:
                    yaml.dump({"metadata": metadata, "error": str(e)}, f)
        else:
            with open(path, "w") as f:
                yaml.dump({"metadata": metadata, "isMenuShowing": True}, f)


editor_names = ["Visual Studio Code", "Code", "VSCodium", "Codium", "code-oss"]


def get_vscode_app() -> ui.App:
    for app in ui.apps(background=False):
        if app.name in editor_names:
            return app

    raise RuntimeError("VSCode must be running")
