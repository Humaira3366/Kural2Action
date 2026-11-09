

def extract_location_text(transcript):
    """
    Extract a location phrase from the citizen's response.
    This is a simple Tamil-specific prototype.
    """

    prefixes = [
        "என் புகார்",
        "எங்கள் புகார்",
        "புகார்"
    ]

    location = transcript.strip()

    for prefix in prefixes:
        if location.startswith(prefix):
            location = location[len(prefix):].strip()
            break

    # Remove common sentence-ending phrases.
    endings = ["உள்ளது.", "உள்ளது", "இருக்கிறது.", "இருக்கிறது"]

    for ending in endings:
        if location.endswith(ending):
            location = location[:-len(ending)].strip()
            break

    return location.strip(" ,.")


def update_complaint_location(complaint, citizen_response):
    if not citizen_response or not citizen_response.strip():
        raise ValueError("Citizen response cannot be empty.")

    complaint["location"] = citizen_response.strip()
    complaint["location_verified"] = False

    if "location" in complaint["missing_fields"]:
        complaint["missing_fields"].remove("location")

    # Wait for explicit citizen confirmation.
    complaint["status"] = "Pending Verification"

    return complaint



if __name__ == "__main__":
    sample_complaint = {
        "complaint_id": "K2A-TEST1234",
        "location": None,
        "missing_fields": ["location"],
        "status": "Pending Verification"
    }

    updated = update_complaint_location(
        sample_complaint,
        "Anna Nagar, near the main bus stop"
    )

    print("\n========== UPDATED COMPLAINT ==========")
    print(updated)
    print("=======================================\n")
