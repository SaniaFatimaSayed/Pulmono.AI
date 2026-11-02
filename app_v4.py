import os
import uuid
import base64

import streamlit as st

from mic_recorder_custom import mic_recorder_custom

from audio_pipeline import run_audio_pipeline
from audio_pipeline_v2 import run_audio_pipeline_from_path
from audio_pipeline_without_pheno import run_audio_pipeline_without_pheno
from audio_pipeline_without_pheno_v2 import run_audio_pipeline_without_pheno_path

# PAGE CONFIG
st.set_page_config(
    page_title="Pulmono.AI",
    layout="wide"
)

# CONFIG
AUDIO_DIR = "outputs/recorded_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

LOGO = "Pulmono.AI.png"

RECORD_SECONDS = 30

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


# HELPERS
def save_audio(audio_bytes):
    path = os.path.join(
        AUDIO_DIR,
        f"{uuid.uuid4()}.wav"
    )

    with open(path, "wb") as f:
        f.write(audio_bytes)

    return path


def reset():
    for k, v in DEFAULT_STATE.items():
        st.session_state[k] = v


# -----------------CSS--------------------------

st.markdown(
    """
    <style>

    .header{

    display:flex;

    align-items:center;

    gap:10px;

    margin-bottom:25px;

    }

    .logo{

    width:85px;

    height:85px;

    border-radius:50%;

    object-fit:cover;

    }

    .title{

    font-size:42px;

    font-weight:700;

    margin:0;

    }

    .subtitle{

    font-size:18px;

    color:gray;

    margin-top:-5px;

    }

    /* Uses Streamlit theme automatically */

    .rainbow-text{

    font-size:20px;

    line-height:1.9;

    font-weight:500;

    color:var(--text-color);

    padding:20px;

    border-radius:10px;

    border:1px solid rgba(150,150,150,.3);

    background:rgba(127,127,127,.08);

    }

    div.stButton>button{

    width:100%;

    height:48px;

    font-size:18px;

    }

    </style>
    """,
    unsafe_allow_html=True
)

# HEADER
with open(LOGO, "rb") as f:
    img = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
<div class="header">

<img src="data:image/png;base64,{img}"
class="logo">

<div>

<div class="title">
Pulmono.AI
</div>

<div class="subtitle">
Voice-based Lung Function Screening
</div>

</div>

</div>
""",
    unsafe_allow_html=True
)

# --------- HOME PAGE --------------
if st.session_state.page == "home":

    st.info(
        "Research prototype only. This tool does not replace clinical spirometry."
    )

    st.markdown("## Choose how you would like to provide your voice sample")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Record Live")

        st.write(
            "Read the Rainbow Passage using your microphone."
        )

        if st.button("Use Microphone"):
            st.session_state.input_mode = "record"

            st.session_state.page = "record"

            st.rerun()

    with col2:

        st.subheader("Upload Recording")

        st.write(
            "Upload an existing WAV, MP3 or M4A recording."
        )

        if st.button("Upload Audio"):
            st.session_state.input_mode = "upload"

            st.session_state.page = "upload"

            st.rerun()


# ------------- RECORD PAGE ------------------
elif st.session_state.page == "record":

    st.header("Record Voice Sample")

    st.info(
        "Please read the Rainbow Passage naturally for approximately 30 seconds.\n\n"
        "Pulmono.AI will automatically analyse only the 15–25 second portion."
    )

    # RAINBOW PASSAGE
    RAINBOW_TEXT = """
        When the sunlight strikes raindrops in the air, they act as a prism and form a rainbow.
        The rainbow is a division of white light into many beautiful colors. These take the
        shape of a long round arch, with its path high above, and its two ends apparently
        beyond the horizon. There is, according to legend, a boiling pot of gold at one end.
        People look, but no one ever finds it. When a man looks for something beyond his
        reach, his friends say he is looking for the pot of gold at the end of the rainbow.
        Throughout the centuries people have explained the rainbow in various ways. Some
        have accepted it as a miracle without physical explanation. To the Hebrews it was a
        token that there would be no more universal floods. The Greeks used to imagine that
        it was a sign from the gods to foretell war or heavy rain.
        """

    st.markdown(
        f"""
        <div class="rainbow-text">
        {RAINBOW_TEXT}
        """,
        unsafe_allow_html=True
    )

    # st.info("""
    # 🎙 Instructions
    #
    # 1. Click **🔴 Start Recording** below. This immediately starts both your
    #    microphone and the 30-second timer.
    # 2. Read the Rainbow Passage naturally.
    # 3. Continue reading for approximately **30 seconds**.
    # 4. Press **⏹ Stop Recording**.
    # 5. Continue to the next page.
    # """)

    # Single custom component: one click both requests the microphone and
    # starts the on-screen timer, since they happen in the same JS click
    # handler in the same browser frame. Returns None until a recording has
    # been stopped, then {"audio_base64": ..., "sample_rate": ..., "format": "wav"}.
    # result = mic_recorder_custom(record_seconds=RECORD_SECONDS, key="custom_recorder")
    #
    # if result is not None and result.get("audio_base64"):
    #     new_bytes = base64.b64decode(result["audio_base64"])
    #
    #     if new_bytes != st.session_state.audio_bytes:
    #         path = save_audio(new_bytes)
    #
    #         st.session_state.audio_path = path
    #         st.session_state.audio_bytes = new_bytes
    #
    #         st.success("Recording saved successfully.")
    #
    # if st.session_state.audio_bytes is not None:
    #     st.audio(
    #         st.session_state.audio_bytes,
    #         format="audio/wav"
    #     )
    #
    # col1, col2 = st.columns(2)
    #
    # with col1:
    #
    #     if st.button("⬅ Back"):
    #         reset()
    #
    #         st.rerun()
    #
    # with col2:
    #
    #     if st.session_state.audio_path is not None:
    #
    #         if st.button("Next ➜"):
    #             st.session_state.page = "phenotype"
    #
    #             st.rerun()

    result = mic_recorder_custom(
        record_seconds=RECORD_SECONDS,
        key="custom_recorder"
    )

    # DEBUG: Check what the recorder returns
    if result is not None:

        st.write("Recorder response type:", type(result))

        if isinstance(result, dict):

            st.write("Recorder response keys:", list(result.keys()))

            if result.get("audio_base64"):

                new_bytes = base64.b64decode(
                    result["audio_base64"]
                )

                if new_bytes != st.session_state.audio_bytes:
                    path = save_audio(new_bytes)

                    st.session_state.audio_path = path
                    st.session_state.audio_bytes = new_bytes

                    st.success("Recording saved successfully!")

            else:
                st.warning("Recorder returned data, but no audio_base64 was found.")

    # Display recording
    if st.session_state.audio_bytes is not None:
        st.audio(
            st.session_state.audio_bytes,
            format="audio/wav"
        )

        st.success("Recording ready for analysis.")

    # Navigation
    col1, col2 = st.columns(2)

    with col1:
        if st.button("⬅ Back"):
            reset()
            st.rerun()

    with col2:
        if st.session_state.audio_bytes is not None:

            if st.button("Next ➜"):
                st.session_state.page = "phenotype"
                st.rerun()

# ---------------- UPLOAD PAGE ----------------
elif st.session_state.page == "upload":

    st.header("Upload Voice Recording")

    st.info(
        "Please upload a WAV, MP3, or M4A recording of you reading the Rainbow Passage."
    )

    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a"]
    )

    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.audio(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:

        if st.button("⬅ Back"):
            reset()

            st.rerun()

    with col2:

        if st.session_state.uploaded_file is not None:

            if st.button("Next ➜"):
                st.session_state.page = "phenotype"

                st.rerun()


# ----------- PHENOTYPE PAGE -----------------

elif st.session_state.page == "phenotype":

    st.header("Optional Patient Information")

    st.info(
        "Pulmono.AI can predict lung function using voice recordings alone. "
        "Providing phenotype information (age, height and weight) may improve prediction accuracy."
    )

    st.header("Patient Information")

    use_pheno = st.radio(
        "Do you have the patient's phenotype information?",
        [
            "Yes",
            "No (use voice-only model)"
        ]
    )

    st.info(
        "Please enter the patient's phenotype information. "
        "These values are combined with the acoustic biomarkers."
    )

    col1, col2 = st.columns(2)

    with col1:

        age = st.number_input(
            "Age",
            min_value=1,
            max_value=120,
            value=30
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=20,
            max_value=250,
            value=70
        )

    with col2:

        height = st.number_input(
            "Height (cm)",
            min_value=50,
            max_value=250,
            value=165
        )

        sex = st.radio(
            "Sex",
            ["Female", "Male"]
        )

    st.divider()

    noise_mode = st.radio(
        "Recording Environment",
        [
            "Quiet environment",
            "Noisy environment"
        ],
        horizontal=True
    )

    patient_info = {

        "age": age,

        "height": height,

        "weight": weight,

        "is_male": 1 if sex == "Male" else 0,

        "is_female": 1 if sex == "Female" else 0,

    }

    left, right = st.columns(2)

    # Back

    with left:

        if st.button("⬅ Back"):

            if st.session_state.input_mode == "record":

                st.session_state.page = "record"

            else:

                st.session_state.page = "upload"

            st.rerun()

    # Run analysis

    with right:

        if st.button("Run Pulmono.AI Analysis"):

            with st.spinner("Running Pulmono.AI..."):

                # RECORDED USING MICROPHONE

                if st.session_state.input_mode == "record":

                    if use_pheno == "Yes":
                        results = run_audio_pipeline_from_path(

                            audio_path=st.session_state.audio_path,

                            noise_mode=noise_mode,

                            patient_info=patient_info,

                            crop_start=15,

                            crop_end=25

                        )

                    else:

                        results = run_audio_pipeline_without_pheno_path(

                            audio_path=st.session_state.audio_path,

                            noise_mode=noise_mode,

                            crop_start=15,

                            crop_end=25

                        )
                # UPLOADED AUDIO
                else:
                    if use_pheno == "Yes":
                        results = run_audio_pipeline(

                            uploaded_file=st.session_state.uploaded_file,

                            noise_mode=noise_mode,

                            patient_info=patient_info

                        )
                    else:
                        results = run_audio_pipeline_without_pheno(

                            uploaded_file=st.session_state.uploaded_file,

                            noise_mode=noise_mode,

                        )

                st.session_state.results = results

                st.session_state.page = "results"

                st.rerun()


# ------------- RESULTS PAGE -------------

elif st.session_state.page == "results":

    st.title("Results")

    results = st.session_state.results

    if results is None:
        st.error("No results available.")
        if st.button("Start again"):
            reset()
            st.rerun()

    else:

        col1, col2 = st.columns(2)

        with col1:

            fev1 = results["fev1"]

            st.metric(
                "Predicted FEV1",
                f"{fev1:.1f}%"
            )

            if fev1 > 81:
                st.write("**Status:** Normal")
            elif 79 <= fev1 <= 81:
                st.write("**Status:** Borderline Normal")
            else:
                st.write("**Status:** Abnormal")

            st.caption(
                f"Confidence: {results['fev1_binary_confidence']:.1f}%"
            )

        with col2:

            fev1_fvc = results["fev1_fvc"]

            st.metric(
                "Predicted FEV1/FVC",
                f"{fev1_fvc:.1f}%"
            )

            if fev1_fvc > 71:
                st.write("**Status:** Normal")
            elif 69 <= fev1_fvc <= 71:
                st.write("**Status:** Borderline Normal")
            else:
                st.write("**Status:** Abnormal")

            st.caption(
                f"Confidence: {results['fev1_fvc_binary_confidence']:.1f}%"
            )


        st.warning(
            "Research prototype only. "
            "This tool does not replace clinical spirometry."
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button("Analyse another recording"):
                reset()

                st.rerun()

        with col2:

            if st.button("Back to phenotype"):
                st.session_state.page = "phenotype"

                st.rerun()
