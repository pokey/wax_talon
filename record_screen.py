import json
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from talon import (
    Context,
    Module,
    actions,
    app,
    cron,
    scope,
    screen,
    settings,
    speech_system,
)
from talon.canvas import Canvas

from .recorder import Recorder, RecordingContext

CALIBRATION_DISPLAY_BACKGROUND_COLOR = "#1b0026"
CALIBRATION_DISPLAY_DURATION = "50ms"

mod = Module()
mod.tag(
    "recording_screen",
    "tag to to indicate that screen is currently being recorded",
)


screenshot_time_stamp_only = mod.setting(
    "screenshot_time_stamp_only",
    type=bool,
    default=True,
    desc="If `True`, don't actually take a screenshot during recording just capture the timestamp so that we can extract it from the video later",
)

ctx = Context()

sleeping_recording_screen_ctx = Context()
sleeping_recording_screen_ctx.matches = r"""
mode: sleep
and tag: user.recording_screen
"""

recording_screen_ctx = Context()
recording_screen_ctx.matches = r"""
tag: user.recording_screen
"""

GIT = "/usr/local/bin/git"

recordings_root_dir = Path.home() / "talon-recording-logs"

recording_start_time: float
recorders: list[Recorder]
recording_context: RecordingContext


def log_object(output_object):
    with open(recording_log_file, "a") as out:
        out.write(json.dumps(output_object) + "\n")


def git(*args: str, cwd: Path):
    return subprocess.run(
        [GIT, *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    ).stdout.strip()


@mod.action_class
class Actions:
    def start_recording(
        recorder_1: Optional[Recorder] = None,
        recorder_2: Optional[Recorder] = None,
        recorder_3: Optional[Recorder] = None,
        recorder_4: Optional[Recorder] = None,
        recorder_5: Optional[Recorder] = None,
    ):
        """Start recording a talon session"""
        global recording_start_time
        global recording_context
        global screenshots_directory
        global recording_log_file
        global current_phrase_id
        global recorders

        recorders = list(
            filter(None, [recorder_1, recorder_2, recorder_3, recorder_4, recorder_5])
        )

        for recorder in recorders:
            recorder.check_can_start()

        recording_log_directory = recordings_root_dir / time.strftime(
            "%Y-%m-%dT%H-%M-%S"
        )
        recording_log_directory.mkdir(parents=True)

        recording_log_file = recording_log_directory / "talon-log.jsonl"

        screenshots_directory = recording_log_directory / "screenshots"
        screenshots_directory.mkdir(parents=True)

        check_and_log_talon_subdirs()

        ctx.tags = ["user.recording_screen"]

        current_phrase_id = None

        recording_context = RecordingContext(
            recording_log_directory, screenshots_directory
        )

        extra_initial_info_fields = {}

        for recorder in recorders:
            actions.sleep("250ms")
            extra_initial_info_fields.update(
                recorder.start_recording(recording_context) or {}
            )

        # Flash a rectangle so that we can synchronize the recording start time
        flash_rect()

        recording_start_time = time.perf_counter()
        start_timestamp_iso = datetime.utcnow().isoformat()

        user_dir: Path = Path(actions.path.talon_user())

        log_object(
            {
                "type": "initialInfo",
                "version": 1,
                "startTimestampISO": start_timestamp_iso,
                "talonDir": str(user_dir.parent),
                **extra_initial_info_fields,
            }
        )

    def record_screen_stop():
        """Stop recording screen"""
        for recorder in recorders:
            recorder.check_can_stop()

        ctx.tags = []

        for recorder in recorders:
            actions.sleep("250ms")
            recorder.stop_recording()

        actions.user.post_record_screen_stop_hook()

    def maybe_capture_phrase(j: Any):
        """Possibly capture a phrase; does nothing unless screen recording is active"""

    def maybe_capture_post_phrase(j: Any):
        """Possibly capture a phrase; does nothing unless screen recording is active"""

    def take_snapshot(path: str, metadata: Any, decorated_marks: list[dict]):
        """Take a snapshot of the current app state"""

    def post_record_screen_start_hook():
        """Hook to run after starting a screen recording"""
        pass

    def post_record_screen_stop_hook():
        """Hook to run after stopping a screen recording"""
        pass


def check_and_log_talon_subdirs():
    for directory in Path(actions.path.talon_user()).iterdir():
        if not directory.is_dir():
            continue

        repo_remote_url = git("config", "--get", "remote.origin.url", cwd=directory)

        if not repo_remote_url:
            continue

        if git("status", "--porcelain", cwd=directory):
            app.notify("ERROR: Please commit all git changes")
            raise Exception("Please commit all git changes")

        commit_sha = git("rev-parse", "HEAD", cwd=directory)

        # Represents the path of the given folder within the git repo in
        # which it is contained. This occurs when we sim link a subdirectory
        # of a repository into our talon user directory such as we do with
        # cursorless talon.
        repo_prefix = git("rev-parse", "--show-prefix", cwd=directory)

        log_object(
            {
                "type": "directoryInfo",
                "localPath": str(directory),
                "localRealPath": str(directory.resolve(strict=True)),
                "repoRemoteUrl": repo_remote_url,
                "repoPrefix": repo_prefix,
                "commitSha": commit_sha,
            }
        )


@sleeping_recording_screen_ctx.action_class("user")
class SleepUserActions:
    def maybe_show_history():
        pass


@ctx.action_class("user")
class UserActions:
    def post_record_screen_start_hook():
        pass

    def post_record_screen_stop_hook():
        pass

    def maybe_capture_phrase(j: Any):
        # Turn this one off globally
        pass

    def maybe_capture_post_phrase(j: Any):
        # Turn this one off globally
        pass

    def take_snapshot(path: str, metadata: Any, decorated_marks: list[dict]):
        # Turn this one off globally
        pass


def json_safe(arg: Any):
    """
    Checks whether arg can be json serialized and if so just returns arg as is
    otherwise returns none

    """
    try:
        json.dumps(arg)
        return arg
    except:
        return None


current_phrase_id: Optional[str] = None


@recording_screen_ctx.action_class("user")
class UserActions:
    def maybe_capture_phrase(j: Any):
        global current_phrase_id

        pre_phrase_start = time.perf_counter() - recording_start_time

        words = j.get("text")

        text = actions.user.history_transform_phrase_text(words)

        word_infos = [
            {
                "start": (
                    words[idx].start - recording_start_time
                    if words[idx].start is not None
                    else None
                ),
                "end": (
                    words[idx].end - recording_start_time
                    if words[idx].end is not None
                    else None
                ),
                "text": str(words[idx]),
            }
            for idx in range(len(words))
        ]

        if text is None:
            try:
                speech_start = j["_ts"] - recording_start_time
            except KeyError:
                speech_start = None

            log_object(
                {
                    "type": "talonIgnoredPhrase",
                    "id": str(uuid.uuid4()),
                    "raw_words": word_infos,
                    "timeOffsets": {
                        "speechStart": speech_start,
                        "prePhraseCallbackStart": pre_phrase_start,
                    },
                    "speechTimeout": settings.get("speech.timeout"),
                }
            )

            current_phrase_id = None

            return

        sim = None
        commands = None
        try:
            sim = speech_system._sim(text)
            commands = actions.user.parse_sim(sim)
        except Exception as e:
            app.notify(f'Couldn\'t sim for "{text}"', f"{e}")

        parsed = j["parsed"]

        if commands is not None:
            for idx, capture_list in enumerate(parsed):
                commands[idx]["captures"] = [
                    json_safe(capture) for capture in capture_list
                ]

        current_phrase_id = str(uuid.uuid4())

        pre_command_screenshot = capture_screen(
            screenshots_directory, recording_start_time
        )

        for recorder in recorders:
            recorder.capture_pre_phrase()

        log_object(
            {
                "type": "talonCommandPhrase",
                "id": current_phrase_id,
                "timeOffsets": {
                    "speechStart": j["_ts"] - recording_start_time,
                    "prePhraseCallbackStart": pre_phrase_start,
                    "prePhraseCallbackEnd": time.perf_counter() - recording_start_time,
                },
                "speechTimeout": settings.get("speech.timeout"),
                "phrase": text,
                "raw_words": word_infos,
                "rawSim": sim,
                "commands": commands,
                "modes": list(scope.get("mode")),
                "tags": list(scope.get("tag")),
                "screenshots": {
                    "decoratedMarks": mark_screenshots,
                    "preCommand": pre_command_screenshot,
                },
            }
        )

    def maybe_capture_post_phrase(j: Any):
        global current_phrase_id

        if current_phrase_id is not None:
            for recorder in recorders:
                recorder.capture_post_phrase()

            post_phrase_start = time.perf_counter() - recording_start_time
            post_command_screenshot = capture_screen(
                screenshots_directory, recording_start_time
            )

            # NB: This object will get merged with the pre-phrase object during
            # postprocessing.  See
            # https://github.com/pokey/voice_vid/blob/079558a2246875fd651bdd7f5d7b76974dc9b3eb/voice_vid/io/parse_transcript.py#L112-L117
            log_object(
                {
                    "id": current_phrase_id,
                    "commandCompleted": True,
                    "timeOffsets": {
                        "postPhraseCallbackStart": post_phrase_start,
                        "postPhraseCallbackEnd": (
                            time.perf_counter() - recording_start_time
                        ),
                    },
                    "screenshots": {
                        "postCommand": post_command_screenshot,
                    },
                }
            )

            current_phrase_id = None


def flash_rect():
    rect = screen.main_screen().rect

    def on_draw(c):
        c.paint.style = c.paint.Style.FILL
        c.paint.color = CALIBRATION_DISPLAY_BACKGROUND_COLOR
        c.draw_rect(rect)
        cron.after(CALIBRATION_DISPLAY_DURATION, canvas.close)

    canvas = Canvas.from_rect(rect)
    canvas.register("draw", on_draw)
    canvas.freeze()


def capture_screen(directory: Path, start_time: float):
    timestamp = time.perf_counter() - start_time

    if screenshot_time_stamp_only.get():
        filename = None
    else:
        img = screen.capture_rect(screen.main_screen().rect)
        date = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S-%f")
        filename = f"{date}.png"
        path = directory / filename
        # NB: Writing the image to the file is expensive so we do it asynchronously
        cron.after("50ms", lambda: img.write_file(path))

    return {
        "filename": filename,
        "timeOffset": timestamp,
    }


last_phrase = None


def on_phrase(j):
    actions.user.maybe_capture_phrase(j)


def on_post_phrase(j):
    actions.user.maybe_capture_post_phrase(j)


speech_system.register("pre:phrase", on_phrase)
speech_system.register("post:phrase", on_post_phrase)
