from talon import Context, actions, ui

ctx = Context()


@ctx.action_class("user")
class Actions:
    def quicktime_check_can_start():
        pass

    def quicktime_check_can_stop():
        pass

    def quicktime_start_recording():
        # Start quicktime screen recording
        actions.key("cmd-shift-5")
        actions.sleep("500ms")
        actions.key("enter")

        actions.sleep("3s")

    def quicktime_stop_recording():
        # Stop quicktime screen recording
        ui.apps(bundle="com.apple.screencaptureui")[0].children.find_one(
            AXRole="AXMenuBarItem"
        ).perform("AXPress")
