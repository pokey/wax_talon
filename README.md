# Wax Talon

Record your Talon sessions. Supports QuickTime, OBS, Cursorless, as well as capturing information about Talon commands, rules, phrase timing, etc. For an example of a video generated using this recorder and its associated [postprocessor](https://github.com/pokey/voice_vid), see https://pokey.github.io/videos/P2QKl-g4CGs/.

**WARNING**: This code relies on undocumented and experimental Taon APIs, so it may break with future versions of Talon.

## Example

Add the following to a Talon file:

```talon
not tag: user.wax_is_recording
-
^record start$:
    cursorless_recorder = user.get_cursorless_recorder(1)
    quicktime_recorder = user.get_quicktime_recorder()
    obs_recorder = user.get_obs_recorder()
    user.wax_start_recording(cursorless_recorder, quicktime_recorder, obs_recorder)
```

And add the following to another Talon file:

```talon
tag: user.wax_is_recording
-
^record stop$: user.wax_stop_recording()
```

This will create a command `"record start"` that will do the following:

- Start QuickTime screen recording
- Start OBS recording (eg to capture face)
- Create a directory within `~/talon-recording-logs` named by the current timestamp in UTC, eg `~/talon-recording-logs/2022-02-23T17-18-00/`
- Capture git SHAs of all directories within `~/.talon/user`
- Flash the screen purple and initialise a performance counter so that all timestamps can be calibrated with the screen recording

Then after each command phrase:

- Cause Cursorless to capture each Cursorless command, including the editor state and the full json payload to VSCode, within a subdir of the above capture directory
- Cause Talon to take a snapshot of VSCode editor state before and after executing every command phrase in the above directory
- Dumps timing information about every command phrase including start and end times, which can be used to generate screenshots from the video or automatically edit the video
- Capture links to the rules that were activated by the command phrase
- Capture other information such as Talon tags, etc
- Quickly flashes all Cursorless marks that were referred to during the command phrase and captures the timestamp of this moment. This information can be used to automatically highlight referenced marks in postprocessing

The above will also enable a command `"record stop"` to stop recording.

You can tweak the above Talonscript to remove any of the recorders, if eg you don't want to capture Cursorless commands, start QuickTime, etc.

## Postprocessing

See https://github.com/pokey/voice_vid.
