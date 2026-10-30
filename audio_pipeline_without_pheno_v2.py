import os
import subprocess
import librosa
import soundfile as sf
import imageio_ffmpeg

from denoiser_module import denoise_audio
from bigru_segmenter import run_bigru_segmentation
from feature_extraction import extract_features_from_audio
from inference import predict_all_models


def ensure_wav(input_path, output_dir="outputs/converted_audio"):
    """
    Convert any incoming audio to a clean 44.1 kHz mono WAV.
    """

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    os.makedirs(output_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base}_converted.wav")

    result = subprocess.run(
        [
            ffmpeg_exe,
            "-y",
            "-i", input_path,
            "-ar", "44100",
            "-ac", "1",
            output_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed to convert {input_path}:\n{result.stderr}"
        )

    return output_path


def crop_audio(audio_path, start_sec=15, end_sec=25, output_dir="outputs/cropped_audio"):
    os.makedirs(output_dir, exist_ok=True)

    # Normalize to WAV first — handles webm/opus (Chrome/Firefox) and
    # mp4/aac (Safari) uniformly, avoids audioread.NoBackendError
    wav_path = ensure_wav(audio_path)

    y, sr = librosa.load(wav_path, sr=44100, mono=True)

    start = int(start_sec * sr)
    end = int(end_sec * sr)
    y_crop = y[start:end]

    base = os.path.splitext(os.path.basename(wav_path))[0]

    output_path = os.path.join(output_dir, f"{base}_15_25s.wav")

    sf.write(output_path, y_crop, sr)

    return output_path


def run_audio_pipeline_without_pheno_path(
    audio_path,
    noise_mode,
    #patient_info,
    crop_start=15,
    crop_end=25
):
    audio_path = crop_audio(
        audio_path,
        start_sec=crop_start,
        end_sec=crop_end
    )

    if noise_mode == "Noisy environment":
        audio_path = denoise_audio(audio_path)

    segments = run_bigru_segmentation(audio_path)

    features = extract_features_from_audio(
        audio_path=audio_path,
        segments=segments,
        #patient_id="uploaded_recording"
    )

    #features.update(patient_info)

    results = predict_all_models(features)

    return results