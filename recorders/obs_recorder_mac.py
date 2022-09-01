from talon import Context, Module, app, ui

from ..types import Recorder

mod = Module()


mod = Module()

ctx = Context()
ctx.matches = r"""
os: mac
"""


@mod.action_class
class Actions:
    def get_obs_recorder() -> Recorder:
        """Returns an object that can be used for recording OBS"""
        pass


@ctx.action_class("user")
class UserActions:
    def get_obs_recorder():
        return ObsRecorder()


def show_obs_menu():
    menu = ui.apps(bundle="com.obsproject.obs-studio")[0].children.find_one(
        AXRole="AXMenuBarItem", AXSubrole="AXMenuExtra"
    )

    try:
        menu.perform("AXPress")
    except:
        pass

    return menu


class ObsRecorder(Recorder):
    def check_can_start(self):
        # Ensure that OBS is running
        try:
            next(app for app in ui.apps(background=False) if app.name == "OBS")
        except StopIteration:
            app.notify("ERROR: Please launch OBS")
            raise

    def start_recording(self):
        # Start OBS face recording
        menu = show_obs_menu()
        menu.children.find_one(AXRole="AXMenuItem", AXTitle="Start Recording").perform(
            "AXPress"
        )

    def stop_recording(self):
        # Stop OBS face recording
        menu = show_obs_menu()
        menu.children.find_one(AXRole="AXMenuItem", AXTitle="Stop Recording").perform(
            "AXPress"
        )
