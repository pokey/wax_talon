import subprocess
from pathlib import Path

from talon import Module, actions, app, ui

from ..types import Recorder, RecordingContext

GIT = "git"

mod = Module()


@mod.action_class
class Actions:
    def get_git_recorder() -> Recorder:
        """
        Returns an object that can be used to take a snapshot of the shas of
        the git subdirectories of talon user directory
        """
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
        # Fails if any directories have uncommitted changes
        for directory in Path(actions.path.talon_user()).iterdir():
            if not directory.is_dir():
                continue

            repo_remote_url = git("config", "--get", "remote.origin.url", cwd=directory)

            if not repo_remote_url:
                continue

            if git("status", "--porcelain", cwd=directory):
                app.notify(
                    f"WARNING: Uncommitted changes to Talon user dir in {directory}"
                )

    def start_recording(self, context: RecordingContext):
        # Capture shas of all subdirectories of `.talon/user` that are `git` directories
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
