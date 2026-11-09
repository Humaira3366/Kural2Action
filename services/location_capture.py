
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GNANI_API_KEY")
BASE_URL = os.getenv(
    "GNANI_BASE_URL",
    "https://api.vachana.ai"
)


def transcribe_audio(audio_path, language_code="ta-IN"):

    if not API_KEY:
        raise ValueError(
            "GNANI_API_KEY is missing from .env"
        )

    if not os.path.exists(audio_path):
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    api_url = f"{BASE_URL}/stt/v3"

    headers = {
        "X-API-Key-ID": API_KEY,
        "X-Source": "playground"
    }

    data = {
        "model": "prisma-v3.0",
        "language_code": language_code,
        "format": "codemix",
        "enable_substitution": "false"
    }

    with open(audio_path, "rb") as audio_file:

        files = {
            "audio_file": (
                os.path.basename(audio_path),
                audio_file,
                "audio/wav"
            )
        }

        response = requests.post(
            api_url,
            headers=headers,
            data=data,
            files=files,
            timeout=120
        )

    response.raise_for_status()

    result = response.json()

    if not result.get("success"):
        raise RuntimeError(
            f"Prisma transcription failed: {result}"
        )

    return result


# Backward compatibility with your existing main.py.
def transcribe_location_audio(audio_path):
    return transcribe_audio(
        audio_path,
        language_code="ta-IN"
    )


if __name__ == "__main__":

    result = transcribe_audio(
        "samples/tamil_complaint.wav",
        language_code="ta-IN"
    )

    print("\n========== PRISMA TRANSCRIPTION ==========")
    print("Success:", result.get("success"))
    print("Transcript:", result.get("transcript"))
    print("Language:", result.get("language"))
    print("==========================================\n")
