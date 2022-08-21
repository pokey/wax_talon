from talon import Context, actions, ui

from .recorder import Recorder

ctx = Context()
ctx.matches = r"""
os: mac
"""


@ctx.action_class("user")
class Actions:
    def get_quicktime_recorder() -> Recorder:
        return QuicktimeRecorder()


class QuicktimeRecorder(Recorder):
    def check_can_start(self):
        pass

    def check_can_stop(self):
        pass

    def start_recording(self):
        # Start quicktime screen recording
        actions.key("cmd-shift-5")
        actions.sleep("500ms")
        actions.key("enter")

        actions.sleep("3s")

    def capture_pre_phrase(self):
        pass

    def capture_post_phrase(self):
        pass

    def stop_recording(self):
        # Stop quicktime screen recording
        ui.apps(bundle="com.apple.screencaptureui")[0].children.find_one(
            AXRole="AXMenuBarItem"
        ).perform("AXPress")
