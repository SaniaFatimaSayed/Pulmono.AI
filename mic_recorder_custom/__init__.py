import os
import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

_mic_recorder_custom = components.declare_component(
    "mic_recorder_custom",
    path=_COMPONENT_DIR,
)


def mic_recorder_custom(record_seconds=30, key=None):
    """
    Single-widget microphone recorder + countdown timer.

    Unlike streamlit-mic-recorder, the "Start Recording" click and the
    getUserMedia() microphone request happen in the exact same click
    handler in the exact same browser frame -- so the visual timer that
    starts alongside it is genuinely synced to the moment recording
    begins, not just to when the widget is shown.

    Returns None until a recording has been stopped, then a dict:
        {
            "audio_base64": str,   # base64-encoded WAV bytes
            "sample_rate": int,
            "format": "wav",
        }
    """
    return _mic_recorder_custom(
        record_seconds=record_seconds,
        key=key,
        default=None,
    )
