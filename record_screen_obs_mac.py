from talon import Context, app, ui

from .recorder import Recorder

ctx = Context()
ctx.matches = r"""
os: mac
"""


def show_obs_menu():
    menu = ui.apps(bundle="com.obsproject.obs-studio")[0].children.find_one(
        AXRole="AXMenuBarItem", AXSubrole="AXMenuExtra"
    )

    try:
        menu.perform("AXPress")
    except:
        pass

    return menu


@ctx.action_class("user")
class Actions:
    def get_obs_recorder() -> Recorder:
        return ObsRecorder()


class ObsRecorder(Recorder):
    def check_can_start(self):
        # Ensure that OBS is running
        try:
            next(app for app in ui.apps(background=False) if app.name == "OBS")
        except StopIteration:
            app.notify("ERROR: Please launch OBS")
            raise

    def check_can_stop(self):
        pass

    def start_recording(self):
        # Start OBS face recording
        menu = show_obs_menu()
        menu.children.find_one(AXRole="AXMenuItem", AXTitle="Start Recording").perform(
            "AXPress"
        )

    def capture_pre_phrase(self):
        pass

    def capture_post_phrase(self):
        pass

    def stop_recording(self):
        # Stop OBS face recording
        menu = show_obs_menu()
        menu.children.find_one(AXRole="AXMenuItem", AXTitle="Stop Recording").perform(
            "AXPress"
        )
