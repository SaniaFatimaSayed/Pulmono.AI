
from pathlib import Path
import streamlit.components.v1 as components

# Resolve the component directory relative to this file
_COMPONENT_DIR = Path(__file__).resolve().parent / "frontend"

# Verify that the frontend exists
_INDEX_FILE = _COMPONENT_DIR / "index.html"

if not _INDEX_FILE.is_file():
    raise FileNotFoundError(
        f"Microphone component frontend not found: {_INDEX_FILE}"
    )

_mic_recorder_custom = components.declare_component(
    "mic_recorder_custom",
    path=str(_COMPONENT_DIR),
)


def mic_recorder_custom(record_seconds=30, key=None):

    return _mic_recorder_custom(
        record_seconds=record_seconds,
        key=key,
        default=None,
    )
