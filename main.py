from services.location_capture import transcribe_location_audio
from services.complaint_extractor import extract_complaint
from services.clarification import generate_clarification
from services.voice_response import generate_voice_response
from services.complaint_updater import (
    extract_location_text,
    update_complaint_location
)
from services.confirmation import confirm_complaint_location
from database.db import initialize_database, save_complaint

def run_kural2action():

    print("\n========== KURAL2ACTION ==========")
    print("Processing citizen complaint...")

    # 1. Transcribe the original complaint.
    result = transcribe_location_audio(
        "samples/tamil_complaint.wav"
    )

    transcript = result["transcript"]

    # 2. Extract complaint information.
    complaint = extract_complaint(
        transcript,
        language="ta-IN"
    )

    print("\nComplaint created:", complaint["complaint_id"])
    print("Category:", complaint["category"])
    print("Duration:", complaint["duration"])

    # 3. Ask for missing information.
    if "location" in complaint["missing_fields"]:

        question = generate_clarification(complaint)

        print("\nKural2Action asks:", question)

        # 4. Speak the clarification using Timbre.
        audio = generate_voice_response(
            question,
            language="ta-IN",
            filename="samples/clarification.wav"
        )

        print("Voice response generated:", audio)

        # 5. Transcribe the citizen's location response.
        location_result = transcribe_location_audio(
            "samples/location_response.wav"
        )

        location_transcript = location_result["transcript"]

        print("\nCitizen response:", location_transcript)

        # 6. Extract and update the location.
        location = extract_location_text(location_transcript)

        complaint = update_complaint_location(
            complaint,
            location
        )

        print("\nExtracted location:", location)

        # 7. Ask for explicit confirmation.
        answer = input(
            "\nIs this location correct? (yes/no): "
        ).strip().lower()

        confirmed = answer in ["yes", "y"]

        complaint = confirm_complaint_location(
            complaint,
            citizen_confirmed=confirmed
        )


    initialize_database()
    save_complaint(complaint)

    print("\nComplaint successfully saved to SQLite!")

    print("\n========== FINAL COMPLAINT ==========")
    print("Complaint ID:", complaint["complaint_id"])
    print("Category:", complaint["category"])
    print("Location:", complaint["location"])
    print("Location verified:", complaint["location_verified"])
    print("Status:", complaint["status"])
    print("=====================================\n")


if __name__ == "__main__":
    run_kural2action()