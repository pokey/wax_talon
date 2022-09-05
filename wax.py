import json
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

from .screenshots import screenshots
from .types import PhraseInfo, Recorder, RecordingContext

CALIBRATION_DISPLAY_BACKGROUND_COLOR = "#1b0026"
CALIBRATION_DISPLAY_DURATION = "50ms"

mod = Module()
mod.tag(
    "wax_is_recording",
    "Indicates that Wax is currently recording",
)


ctx = Context()

recording_screen_ctx = Context()
recording_screen_ctx.matches = r"""
tag: user.wax_is_recording
"""

recordings_root_dir = Path.home() / "talon-recording-logs"

recorders: list[Recorder]
recording_context: RecordingContext
recording_start_time: float
recording_log_file: Path
current_phrase_info: Optional[PhraseInfo] = None


@mod.action_class
class Actions:
    def wax_start_recording(
        recorder_1: Optional[Recorder] = None,
        recorder_2: Optional[Recorder] = None,
        recorder_3: Optional[Recorder] = None,
        recorder_4: Optional[Recorder] = None,
        recorder_5: Optional[Recorder] = None,
    ):
        """Start recording a talon session"""
        global recorders
        global recording_context
        global recording_start_time
        global recording_log_file
        global current_phrase_info
        global screenshots

        non_null_recorders = list(
            filter(None, [recorder_1, recorder_2, recorder_3, recorder_4, recorder_5])
        ) + [actions.user.get_git_recorder()]

        # Put recorders with calibration display last so they will show up in
        # any screen recording
        recorders = [
            recorder
            for recorder in non_null_recorders
            if not recorder.has_calibration_display
        ] + [
            recorder
            for recorder in non_null_recorders
            if recorder.has_calibration_display
        ]

        try:
            for recorder in recorders:
                recorder.check_can_start()
        except Exception as e:
            app.notify(f"ERROR: {e}")
            raise e

        recording_log_directory = recordings_root_dir / time.strftime(
            "%Y-%m-%dT%H-%M-%S"
        )
        recording_log_directory.mkdir(parents=True)

        recording_log_file = recording_log_directory / "talon-log.jsonl"

        ctx.tags = ["user.wax_is_recording"]

        current_phrase_info = None

        recording_context = RecordingContext(recording_log_directory)

        active_recorders = []

        try:
            for recorder in recorders:
                actions.sleep("250ms")
                recorder.start_recording(recording_context)
                active_recorders.append(recorder)

            # Flash a rectangle so that we can synchronize the recording start time
            flash_rect()

            user_dir: Path = Path(actions.path.talon_user())

            actions.user.wax_log_object(
                {
                    "type": "initialInfo",
                    "version": 2,
                    "talonDir": str(user_dir.parent),
                }
            )
        except Exception as e:
            # In case of error, stop any recorders that we started
            for recorder in active_recorders:
                actions.sleep("250ms")
                try:
                    recorder.check_can_stop()
                    recorder.stop_recording()
                except:
                    pass

            app.notify(f"ERROR: {e}")

            raise e

    def wax_stop_recording():
        """Stop recording screen"""
        for recorder in recorders:
            recorder.check_can_stop()

        ctx.tags = []

        for recorder in recorders:
            actions.sleep("250ms")
            recorder.stop_recording()

    def wax_log_object(output_object: dict):
        """Log an object to the wax recording log"""
        with open(recording_log_file, "a") as out:
            out.write(json.dumps(output_object) + "\n")

    def private_wax_maybe_capture_phrase(j: Any):
        """Possibly capture a phrase; does nothing unless screen recording is active"""

    def private_wax_maybe_capture_post_phrase(j: Any):
        """Possibly capture a phrase; does nothing unless screen recording is active"""


def finish_init(canvas: Canvas) -> None:
    # NB: We record the initial time stamp right before we close the purple
    # flash so that we can guarantee that the timestamp is while the flash is
    # displaying
    global recording_start_time

    recording_start_time = time.perf_counter()
    start_timestamp_iso = datetime.utcnow().isoformat()

    screenshots.init(recording_context, recording_start_time)

    actions.user.wax_log_object(
        {
            "type": "initialTiming",
            "startTimestampISO": start_timestamp_iso,
        }
    )

    canvas.close()


def flash_rect():
    rect = screen.main_screen().rect

    def on_draw(c):
        c.paint.style = c.paint.Style.FILL
        c.paint.color = CALIBRATION_DISPLAY_BACKGROUND_COLOR
        c.draw_rect(rect)
        cron.after(CALIBRATION_DISPLAY_DURATION, lambda: finish_init(canvas))

    canvas = Canvas.from_rect(rect)
    canvas.register("draw", on_draw)
    canvas.freeze()


@ctx.action_class("user")
class UserActions:
    def private_wax_maybe_capture_phrase(j: Any):
        # Turn this one off globally
        pass

    def private_wax_maybe_capture_post_phrase(j: Any):
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


@recording_screen_ctx.action_class("user")
class RecordingUserActions:
    def private_wax_maybe_capture_phrase(j: Any):
        global current_phrase_info

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

            actions.user.wax_log_object(
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

            current_phrase_info = None

            return

        sim = None
        commands = None
        try:
            sim = speech_system._sim(text)
            commands = actions.user.parse_sim(sim)
        except Exception as e:
            app.notify(f'Couldn\'t sim for "{text}"', f"{e}")

        parsed = list(j["parsed"])

        if commands is not None:
            for idx, capture_list in enumerate(parsed):
                commands[idx]["captures"] = [
                    json_safe(capture) for capture in capture_list
                ]

        phrase_id = str(uuid.uuid4())

        current_phrase_info = PhraseInfo(phrase_id, parsed)

        with screenshots.init_object() as screenshots_object:
            screenshots.take_screenshot("preCommand")

            for recorder in recorders:
                recorder.capture_pre_phrase(current_phrase_info)

        actions.user.wax_log_object(
            {
                "type": "talonCommandPhrase",
                "id": phrase_id,
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
                "screenshots": screenshots_object,
            }
        )

    def private_wax_maybe_capture_post_phrase(j: Any):
        global current_phrase_info

        if current_phrase_info is not None:
            post_phrase_start = time.perf_counter() - recording_start_time

            with screenshots.init_object() as screenshots_object:
                for recorder in recorders:
                    recorder.capture_post_phrase(current_phrase_info)

                screenshots.take_screenshot("postCommand")

            # NB: This object will get merged with the pre-phrase object during
            # postprocessing.  See
            # https://github.com/pokey/voice_vid/blob/079558a2246875fd651bdd7f5d7b76974dc9b3eb/voice_vid/io/parse_transcript.py#L112-L117
            actions.user.wax_log_object(
                {
                    "id": current_phrase_info.phrase_id,
                    "commandCompleted": True,
                    "timeOffsets": {
                        "postPhraseCallbackStart": post_phrase_start,
                        "postPhraseCallbackEnd": (
                            time.perf_counter() - recording_start_time
                        ),
                    },
                    "screenshots": screenshots_object,
                }
            )

            current_phrase_info = None


last_phrase = None


def on_phrase(j):
    actions.user.private_wax_maybe_capture_phrase(j)


def on_post_phrase(j):
    actions.user.private_wax_maybe_capture_post_phrase(j)


speech_system.register("pre:phrase", on_phrase)
speech_system.register("post:phrase", on_post_phrase)
