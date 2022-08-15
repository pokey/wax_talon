from talon import Context, actions, ui

ctx = Context()


@ctx.action_class("user")
class Actions:
    def cursorless_check_can_start():
        # VSCode needs to be running
        get_vscode_app()

    def cursorless_check_can_stop():
        # VSCode needs to be running
        get_vscode_app()

    def cursorless_start_recording():
        # Need VSCode in front
        actions.user.switcher_focus_app(get_vscode_app())

        # Start cursorless recording
        return actions.user.vscode_get(
            "cursorless.recordTestCase",
            {
                "isSilent": True,
                "directory": str(commands_directory),
                "extraSnapshotFields": ["timeOffsetSeconds"],
                "showCalibrationDisplay": True,
            },
        )

    def cursorless_stop_recording():
        # Need VSCode in front
        actions.user.switcher_focus_app(get_vscode_app())

        # Stop cursorless recording
        actions.user.vscode("cursorless.recordTestCase")


editor_names = ["Visual Studio Code", "Code", "VSCodium", "Codium", "code-oss"]


def get_vscode_app() -> ui.App:
    for app in ui.apps(background=False):
        if app.name in editor_names:
            return app

    raise RuntimeError("Draft editor is not running")
