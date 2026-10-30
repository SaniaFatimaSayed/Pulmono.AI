import os
import uuid

from feature_extraction import extract_features_from_audio
from inference_without_pheno import predict_all_models

# later import these properly
from denoiser_module import denoise_audio
from bigru_segmenter import run_bigru_segmentation


OUTPUT_DIR = "outputs/uploaded_audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_uploaded_file(uploaded_file):
    file_id = str(uuid.uuid4())
    file_ext = uploaded_file.name.split(".")[-1]
    file_path = os.path.join(OUTPUT_DIR, f"{file_id}.{file_ext}")

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def run_audio_pipeline_without_pheno(uploaded_file, noise_mode):
    audio_path = save_uploaded_file(uploaded_file)

    # 1. Optional denoising
    if noise_mode == "Noisy environment":
        audio_path = denoise_audio(audio_path)

    # 2. BiGRU segmentation
    segments = run_bigru_segmentation(audio_path)

    # 3. Feature extraction
    features = extract_features_from_audio(
        audio_path=audio_path,
        segments=segments,
        #patient_id="uploaded_audio"
    )

    # 4. Add clinical/demographic features
    #features.update(patient_info)

    # 5. Predict using all models
    results = predict_all_models(features)

    return results