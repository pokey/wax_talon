# Wax Talon

Record your Talon sessions. Supports QuickTime, OBS, Cursorless, as well as capturing information about Talon commands, rules, phrase timing, etc. For an example of a video generated using this recorder and its associated [postprocessor](https://github.com/pokey/voice_vid), see https://pokey.github.io/videos/P2QKl-g4CGs/. For an example of the raw output of this recording code, see [the example](examples/2022-09-04T10-20-54/).

**WARNING**: This code relies on undocumented and experimental Taon APIs, so it may break with future versions of Talon.

Note that the OBS recorder currently only works on MacOS, as it relies on Mac accessibility APIs to start and stop recording.

## Example

Add the following to a Talon file:

```talon
not tag: user.wax_is_recording
-
^record start$:
    cursorless_recorder = user.wax_cursorless_recorder()
    quicktime_recorder = user.wax_quicktime_recorder()
    obs_recorder = user.wax_obs_recorder()
    user.wax_start_recording(cursorless_recorder, quicktime_recorder, obs_recorder)
```

And add the following to another Talon file:

```talon
tag: user.wax_is_recording
-
^record stop$: user.wax_stop_recording()
```

These files will create commands `"record start"` and `"record stop"`. The `"record start"` command will do the following:

- Start QuickTime screen recording. The location of this recording will depend on your default QuickTime directory, for example `~/Desktop`.
- Start OBS recording (eg to capture face). The location of this recording will depend on your default OBS directory, for example `~/Movies`.
- Create a subdirectory of `~/talon-recording-logs` to capture information about the current recording. See below for more on what we capture. The directory will be named for the current timestamp in UTC, eg `~/talon-recording-logs/2022-02-23T17-18-00/`
- Create a `talon-log.jsonl` file within the above directory, where most information will be captured.
- Capture git SHAs of all subdirectories of `~/.talon/user`. This information will appear in the above `talon-log.jsonl` file
- Flash the screen purple. All timestamps captured below will be represented as seconds from this purple flash. This way all timestamps can be precisely reconciled to your screen recording.

Then after each command phrase:

- Cause Cursorless to capture each Cursorless command, including the editor state and the full json payload to VSCode, within a subdir of the above capture directory
- Cause Talon to take a snapshot of VSCode editor state before and after executing every command phrase in the above directory
- Dumps timing information about every command phrase including start and end times, which can be used to generate screenshots from the video or automatically edit the video
- Capture links to the rules that were activated by the command phrase
- Capture other information such as Talon tags, etc
- Quickly flashes all Cursorless marks that were referred to during the command phrase and captures the timestamp of this moment. This information can be used to automatically highlight referenced marks in postprocessing

You can tweak the above Talonscript to remove any of the recorders, if eg you don't want to capture Cursorless commands, start QuickTime, etc.

## Postprocessing

See https://github.com/pokey/voice_vid.

## Making a custom recorder

See the examples in [`recorders`](recorders).
