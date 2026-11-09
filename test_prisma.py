import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GNANI_API_KEY")
BASE_URL = os.getenv(
    "GNANI_BASE_URL",
    "https://api.vachana.ai"
)

if not API_KEY:
    raise ValueError("GNANI_API_KEY is missing in .env")

API_URL = f"{BASE_URL}/stt/v3"

headers = {
    "X-API-Key-ID": API_KEY,
    "X-Source": "playground"
}

audio_path = "samples/tamil_complaint.wav"

data = {
    "model": "prisma-v3.0",
    "language_code": "ta-IN",
    "format": "codemix",
    "enable_substitution": "false"
}

try:
    with open(audio_path, "rb") as audio_file:

        files = {
            "audio_file": (
                "tamil_complaint.wav",
                audio_file,
                "audio/wav"
            )
        }

        response = requests.post(
            API_URL,
            headers=headers,
            data=data,
            files=files,
            timeout=120
        )

    response.raise_for_status()

    result = response.json()

    print("\n========== PRISMA RESULT ==========")

    print("Success:", result.get("success"))
    print("Transcript:", result.get("transcript"))
    print("Detected language:", result.get("detected_language_code"))
    print("Model:", result.get("model"))

    print("===================================\n")

except requests.exceptions.RequestException as error:
    print("API request failed:", error)

    if error.response is not None:
        print("Status:", error.response.status_code)
        print("Response:", error.response.text)