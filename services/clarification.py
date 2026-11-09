
def generate_clarification(complaint):
    """
    Generate a follow-up question based on missing complaint details.
    """

    missing_fields = complaint.get("missing_fields", [])
    language = complaint.get("language", "en-IN")

    if "location" in missing_fields:
        if language == "ta-IN":
            question = "தயவுசெய்து உங்கள் தெருவின் பெயர் அல்லது அருகிலுள்ள அடையாளத்தைக் கூறுங்கள்."
        else:
            question = "Please tell us your street name or a nearby landmark."

    elif "duration" in missing_fields:
        if language == "ta-IN":
            question = "இந்தப் பிரச்சினை எவ்வளவு நாட்களாக உள்ளது?"
        else:
            question = "How long has this issue existed?"

    elif "issue_category_confirmation" in missing_fields:
        if language == "ta-IN":
            question = "தயவுசெய்து புகாரின் வகையை இன்னும் கொஞ்சம் விளக்க முடியுமா?"
        else:
            question = "Could you explain the type of issue in more detail?"

    else:
        if language == "ta-IN":
            question = "உங்கள் புகார் உறுதிப்படுத்தத் தயாராக உள்ளது."
        else:
            question = "Your complaint is ready for confirmation."

    return question


if __name__ == "__main__":
    sample_complaint = {
        "language": "ta-IN",
        "missing_fields": ["location"]
    }

    question = generate_clarification(sample_complaint)

    print("\n========== KURAL2ACTION CLARIFICATION ==========")
    print("Generated Question:", question)
    print("================================================\n")
