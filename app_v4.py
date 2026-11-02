import os
import io
import time
import uuid
import wave
import base64

import streamlit as st

from audio_pipeline import run_audio_pipeline
from audio_pipeline_v2 import run_audio_pipeline_from_path
from audio_pipeline_without_pheno import run_audio_pipeline_without_pheno
from audio_pipeline_without_pheno_v2 import run_audio_pipeline_without_pheno_path

# Native recorder (Streamlit >= 1.39) is the most robust option.
# The custom component is only used as a fallback on older versions.
USE_NATIVE_RECORDER = hasattr(st, "audio_input")
if not USE_NATIVE_RECORDER:
    from mic_recorder_custom import mic_recorder_custom

# PAGE CONFIG
st.set_page_config(page_title="Pulmono.AI", layout="wide")

# CONFIG
AUDIO_DIR = "outputs/recorded_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

LOGO = "Pulmono.AI.png"
RECORD_SECONDS = 30
CROP_START = 15
CROP_END = 25

# Thresholds
FEV1_NORMAL, FEV1_BORDERLINE = 81, 79
FEV1_FVC_NORMAL, FEV1_FVC_BORDERLINE = 71, 69

RAINBOW_TEXT = (
    "When the sunlight strikes raindrops in the air, they act as a prism and form "
    "a rainbow. The rainbow is a division of white light into many beautiful colors. "
    "These take the shape of a long round arch, with its path high above, and its "
    "two ends apparently beyond the horizon. There is, according to legend, a "
    "boiling pot of gold at one end. People look, but no one ever finds it. When a "
    "man looks for something beyond his reach, his friends say he is looking for "
    "the pot of gold at the end of the rainbow. Throughout the centuries people "
    "have explained the rainbow in various ways. Some have accepted it as a "
    "miracle without physical explanation. To the Hebrews it was a token that "
    "there would be no more universal floods. The Greeks used to imagine that it "
    "was a sign from the gods to foretell war or heavy rain."
)

# SESSION STATE
DEFAULT_STATE = {
    "page": "home",
    "input_mode": None,
    "audio_path": None,
    "audio_bytes": None,
    "uploaded_file": None,
    "results": None,
}

for k, v in DEFAULT_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Changing this number gives the recorder widget a fresh key, which clears it.
if "recorder_nonce" not in st.session_state:
    st.session_state.recorder_nonce = 0


# HELPERS
def save_audio(audio_bytes):  # only called right before analysis
    path = os.path.join(AUDIO_DIR, f"{uuid.uuid4()}.wav")
    with open(path, "wb") as f:
        f.write(audio_bytes)
    return path


def wav_duration(audio_bytes):
    """Return duration in seconds for WAV bytes, or None if unreadable."""
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None


def delete_file(path):
    """Delete a file if it exists; never raise."""
    if path:
        try:
            os.remove(path)
        except OSError:
            pass


def cleanup_stale_files(max_age_seconds=3600):
    """Safety net: remove leftover audio (e.g. from a crashed or abandoned session)."""
    now = time.time()
    for name in os.listdir(AUDIO_DIR):
        path = os.path.join(AUDIO_DIR, name)
        try:
            if os.path.isfile(path) and now - os.path.getmtime(path) > max_age_seconds:
                os.remove(path)
        except OSError:
            pass


def wipe_audio():
    """Remove all audio held by this session (disk and memory)."""
    delete_file(st.session_state.get("audio_path"))
    st.session_state.audio_path = None
    st.session_state.audio_bytes = None
    st.session_state.uploaded_file = None
    st.session_state.recorder_nonce += 1  # clears the recorder / uploader widgets


def reset():
    wipe_audio()
    for k, v in DEFAULT_STATE.items():
        st.session_state[k] = v


def go(page):
    st.session_state.page = page
    st.rerun()


def classify(value, normal_above, borderline_from):
    if value > normal_above:
        return "Normal"
    if value >= borderline_from:
        return "Borderline Normal"
    return "Abnormal"


cleanup_stale_files()

# CSS
st.markdown(
    """
    <style>
    .header{display:flex;align-items:center;gap:10px;margin-bottom:25px;}
    .logo{width:85px;height:85px;border-radius:50%;object-fit:cover;}
    .title{font-size:42px;font-weight:700;margin:0;}
    .subtitle{font-size:18px;color:gray;margin-top:-5px;}
    .rainbow-text{
        font-size:20px;line-height:1.9;font-weight:500;
        color:var(--text-color);padding:20px;border-radius:10px;
        border:1px solid rgba(150,150,150,.3);
        background:rgba(127,127,127,.08);
    }
    div.stButton>button{width:100%;height:48px;font-size:18px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# HEADER
if os.path.exists(LOGO):
    with open(LOGO, "rb") as f:
        img = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{img}" class="logo">'
else:
    logo_html = ""

st.markdown(
    f"""
<div class="header">
{logo_html}
<div>
<div class="title">Pulmono.AI</div>
<div class="subtitle">Voice-based Lung Function Screening</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

page = st.session_state.page

# ---------------- HOME PAGE ----------------
if page == "home":

    st.info("Research prototype only. This tool does not replace clinical spirometry.")
    st.markdown("## Choose how you would like to provide your voice sample")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Record Live")
        st.write("Read the Rainbow Passage using your microphone.")
        if st.button("Use Microphone", key="btn_mic"):
            st.session_state.input_mode = "record"
            go("record")

    with col2:
        st.subheader("Upload Recording")
        st.write("Upload an existing WAV, MP3 or M4A recording.")
        if st.button("Upload Audio", key="btn_upload"):
            st.session_state.input_mode = "upload"
            go("upload")


# ---------------- RECORD PAGE ----------------
elif page == "record":

    st.header("Record Voice Sample")

    st.info(
        f"Please read the Rainbow Passage naturally for approximately {RECORD_SECONDS} seconds.\n\n"
        f"Pulmono.AI will automatically analyse only the {CROP_START}–{CROP_END} second portion."
    )

    st.markdown(
        f'<div class="rainbow-text">{RAINBOW_TEXT}</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    rec_key = f"recorder_{st.session_state.recorder_nonce}"

    if USE_NATIVE_RECORDER:
        st.caption(
            f"Press the microphone button, read the passage for about {RECORD_SECONDS} "
            "seconds, then press stop."
        )
        try:
            audio = st.audio_input("Record your voice", sample_rate=16000, key=rec_key)
        except TypeError:  # older Streamlit without the sample_rate argument
            audio = st.audio_input("Record your voice", key=rec_key)

        if audio is not None:
            new_bytes = audio.getvalue()
            st.session_state.audio_bytes = new_bytes
    else:
        result = mic_recorder_custom(record_seconds=RECORD_SECONDS, key=rec_key)

        if isinstance(result, dict) and result.get("audio_base64"):
            new_bytes = base64.b64decode(result["audio_base64"])
            st.session_state.audio_bytes = new_bytes

    if st.session_state.audio_bytes is not None:
        duration = wav_duration(st.session_state.audio_bytes)
        if duration is not None and duration < CROP_END:
            st.warning(
                f"Your recording is {duration:.0f}s long, but the analysis needs at least "
                f"{CROP_END}s. Please record again and keep reading for about "
                f"{RECORD_SECONDS}s."
            )
        else:
            st.success("Recording ready for analysis.")

        if not USE_NATIVE_RECORDER:
            st.audio(st.session_state.audio_bytes, format="audio/wav")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Back", key="rec_back"):
            reset()
            st.rerun()

    with col2:
        if st.session_state.audio_bytes is not None:
            if st.button("Next ➜", key="rec_next"):
                go("phenotype")


# ---------------- UPLOAD PAGE ----------------
elif page == "upload":

    st.header("Upload Voice Recording")

    st.info(
        "Please upload a WAV, MP3, or M4A recording of you reading the Rainbow Passage."
    )

    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a"],
        key=f"uploader_{st.session_state.recorder_nonce}",
    )

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.audio(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Back", key="up_back"):
            reset()
            st.rerun()

    with col2:
        if st.session_state.uploaded_file is not None:
            if st.button("Next ➜", key="up_next"):
                go("phenotype")


# ---------------- PHENOTYPE PAGE ----------------
elif page == "phenotype":

    st.header("Optional Patient Information")

    st.info(
        "Pulmono.AI can predict lung function using voice recordings alone. "
        "Providing phenotype information (age, height and weight) may improve "
        "prediction accuracy."
    )

    use_pheno = st.radio(
        "Do you have the patient's phenotype information?",
        ["Yes", "No (use voice-only model)"],
        key="use_pheno",
    )
    with_pheno = use_pheno == "Yes"

    patient_info = None

    if with_pheno:
        st.info(
            "Please enter the patient's phenotype information. "
            "These values are combined with the acoustic biomarkers."
        )

        col1, col2 = st.columns(2)

        with col1:
            age = st.number_input("Age", min_value=1, max_value=120, value=30, key="age")
            weight = st.number_input(
                "Weight (kg)", min_value=20, max_value=250, value=70, key="weight"
            )

        with col2:
            height = st.number_input(
                "Height (cm)", min_value=50, max_value=250, value=165, key="height"
            )
            sex = st.radio("Sex", ["Female", "Male"], key="sex")

        patient_info = {
            "age": age,
            "height": height,
            "weight": weight,
            "is_male": 1 if sex == "Male" else 0,
            "is_female": 1 if sex == "Female" else 0,
        }

    st.divider()

    noise_mode = st.radio(
        "Recording Environment",
        ["Quiet environment", "Noisy environment"],
        horizontal=True,
        key="noise_mode",
    )

    left, right = st.columns(2)

    with left:
        if st.button("⬅ Back", key="ph_back"):
            go("record" if st.session_state.input_mode == "record" else "upload")

    run_clicked = False
    with right:
        run_clicked = st.button("Run Pulmono.AI Analysis", key="run_analysis")

    # Run outside the column context so errors/spinner render full width
    if run_clicked:
        results = None
        audio_path = None
        try:
            with st.spinner("Running Pulmono.AI..."):

                # Write the recording to disk only for the duration of the analysis
                if st.session_state.input_mode == "record":
                    audio_path = save_audio(st.session_state.audio_bytes)

                if st.session_state.input_mode == "record":
                    if with_pheno:
                        results = run_audio_pipeline_from_path(
                            audio_path=audio_path,
                            noise_mode=noise_mode,
                            patient_info=patient_info,
                            crop_start=CROP_START,
                            crop_end=CROP_END,
                        )
                    else:
                        results = run_audio_pipeline_without_pheno_path(
                            audio_path=audio_path,
                            noise_mode=noise_mode,
                            crop_start=CROP_START,
                            crop_end=CROP_END,
                        )
                else:
                    if with_pheno:
                        results = run_audio_pipeline(
                            uploaded_file=st.session_state.uploaded_file,
                            noise_mode=noise_mode,
                            patient_info=patient_info,
                        )
                    else:
                        results = run_audio_pipeline_without_pheno(
                            uploaded_file=st.session_state.uploaded_file,
                            noise_mode=noise_mode,
                        )
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.exception(e)
        else:
            st.session_state.results = results
            wipe_audio()  # recording no longer needed once results exist
            go("results")
        finally:
            delete_file(audio_path)  # deleted even if the analysis failed


# ---------------- RESULTS PAGE ----------------
elif page == "results":

    st.title("Results")

    results = st.session_state.results

    if results is None:
        st.error("No results available.")
        if st.button("Start again", key="res_restart"):
            reset()
            st.rerun()

    else:
        col1, col2 = st.columns(2)

        with col1:
            fev1 = results["fev1"]
            st.metric("Predicted FEV1", f"{fev1:.1f}%")
            st.write(f"**Status:** {classify(fev1, FEV1_NORMAL, FEV1_BORDERLINE)}")
            st.caption(f"Confidence: {results['fev1_binary_confidence']:.1f}%")

        with col2:
            fev1_fvc = results["fev1_fvc"]
            st.metric("Predicted FEV1/FVC", f"{fev1_fvc:.1f}%")
            st.write(
                f"**Status:** {classify(fev1_fvc, FEV1_FVC_NORMAL, FEV1_FVC_BORDERLINE)}"
            )
            st.caption(f"Confidence: {results['fev1_fvc_binary_confidence']:.1f}%")

        st.warning(
            "Research prototype only. This tool does not replace clinical spirometry."
        )

        st.caption("Your recording has been deleted and is not stored.")

        if st.button("Analyse another recording", key="res_again"):
            reset()
            st.rerun()
