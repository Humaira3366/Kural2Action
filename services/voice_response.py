
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GNANI_API_KEY")
BASE_URL = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai")

def generate_voice_response(text, language="ta-IN", filename="samples/clarification.wav"):

    if not API_KEY:
        raise ValueError("GNANI_API_KEY is missing from .env")

    api_url = f"{BASE_URL}/api/v1/tts/inference"

    headers = {
        "X-API-Key-ID": API_KEY,
        "X-Source": "playground",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "voice": "Shivani",
        "model": "timbre-v3.0",
        "language": language,
        "speed": 1.0,
        "audio_config": {
            "sample_rate": 48000,
            "num_channels": 1,
            "sample_width": 2,
            "encoding": "linear_pcm",
            "container": "wav"
        }
    }

    response = requests.post(
        api_url,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "wb") as audio_file:
        audio_file.write(response.content)

    return filename


if __name__ == "__main__":
    question = "தயவுசெய்து உங்கள் தெருவின் பெயர் அல்லது அருகிலுள்ள அடையாளத்தைக் கூறுங்கள்."

    output = generate_voice_response(question)

    print("\n========== KURAL2ACTION VOICE RESPONSE ==========")
    print("Audio generated:", output)
    print("=================================================\n")
