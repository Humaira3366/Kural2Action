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

API_URL = f"{BASE_URL}/api/v1/tts/inference"

headers = {
    "X-API-Key-ID": API_KEY,
    "X-Source": "playground",
    "Content-Type": "application/json"
}

payload = {
    "text": "உங்கள் புகார் பதிவு செய்யப்பட்டுள்ளது. விரைவில் நடவடிக்கை எடுக்கப்படும்.",
    "voice": "Shivani",
    "model": "timbre-v3.0",
    "language": "ta-IN",
    "speed": 1.0,
    "audio_config": {
        "sample_rate": 48000,
        "num_channels": 1,
        "sample_width": 2,
        "encoding": "linear_pcm",
        "container": "wav"
    }
}

try:
    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    output_path = "samples/generated_response.wav"

    with open(output_path, "wb") as audio_file:
        audio_file.write(response.content)

    print("\n========== TIMBRE RESULT ==========")
    print("Status:", response.status_code)
    print("Audio saved:", output_path)
    print("Audio size:", len(response.content), "bytes")
    print("===================================\n")

except requests.exceptions.RequestException as error:
    print("TTS request failed:", error)

    if error.response is not None:
        print("Status:", error.response.status_code)
        print("Response:", error.response.text)