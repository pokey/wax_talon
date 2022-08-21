import subprocess
from pathlib import Path

from talon import Module, actions, app, ui

from ..types import Recorder

GIT = "/usr/local/bin/git"

mod = Module()


@mod.action_class
class Actions:
    def get_git_recorder() -> Recorder:
        return GitRecorder()


def git(*args: str, cwd: Path):
    return subprocess.run(
        [GIT, *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    ).stdout.strip()


class GitRecorder(Recorder):
    def check_can_start(self):
        check_talon_subdirs()

    def start_recording(self):
        log_talon_subdirs()

    def capture_pre_phrase(self):
        pass

    def capture_post_phrase(self):
        pass

    def check_can_stop(self):
        pass

    def stop_recording(self):
        pass


def check_talon_subdirs():
    for directory in Path(actions.path.talon_user()).iterdir():
        if not directory.is_dir():
            continue

        repo_remote_url = git("config", "--get", "remote.origin.url", cwd=directory)

        if not repo_remote_url:
            continue

        if git("status", "--porcelain", cwd=directory):
            app.notify("ERROR: Please commit all git changes")
            raise Exception("Please commit all git changes")


def log_talon_subdirs():
    for directory in Path(actions.path.talon_user()).iterdir():
        if not directory.is_dir():
            continue

        repo_remote_url = git("config", "--get", "remote.origin.url", cwd=directory)

        if not repo_remote_url:
            continue

        commit_sha = git("rev-parse", "HEAD", cwd=directory)

        # Represents the path of the given folder within the git repo in
        # which it is contained. This occurs when we sim link a subdirectory
        # of a repository into our talon user directory such as we do with
        # cursorless talon.
        repo_prefix = git("rev-parse", "--show-prefix", cwd=directory)

        actions.user.wax_log_object(
            {
                "type": "directoryInfo",
                "localPath": str(directory),
                "localRealPath": str(directory.resolve(strict=True)),
                "repoRemoteUrl": repo_remote_url,
                "repoPrefix": repo_prefix,
                "commitSha": commit_sha,
            }
        )
