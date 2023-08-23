from talon import Context, Module, actions, ui

from ..types import Recorder, RecordingContext

mod = Module()

ctx = Context()
ctx.matches = r"""
os: mac
"""


@mod.action_class
class Actions:
    def wax_quicktime_recorder() -> Recorder:
        """Returns an object that can be used for recording quicktime"""
        pass


@ctx.action_class("user")
class UserActions:
    def wax_quicktime_recorder():
        return QuicktimeRecorder()


class QuicktimeRecorder(Recorder):
    def start_recording(self, context: RecordingContext):
        # Start quicktime screen recording
        actions.key("cmd-shift-5")
        actions.sleep("500ms")
        actions.key("enter")

        actions.sleep("3s")

    def stop_recording(self):
        # Stop quicktime screen recording
        ui.apps(bundle="com.apple.screencaptureui")[-1].children.find_one(
            AXRole="AXMenuBarItem"
        ).perform("AXPress")
