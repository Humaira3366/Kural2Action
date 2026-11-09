
from services.location_capture import transcribe_location_audio
from services.complaint_updater import extract_location_text

result = transcribe_location_audio(
    "samples/location_response.wav"
)

transcript = result["transcript"]
location = extract_location_text(transcript)

print("\n========== LOCATION EXTRACTION ==========")
print("Original transcript:", transcript)
print("Extracted location:", location)
print("==========================================")
