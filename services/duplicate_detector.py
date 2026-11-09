
import re
from difflib import SequenceMatcher


def normalise_text(text):
    """Clean text while preserving Tamil and Unicode characters."""

    if not text:
        return ""

    text = str(text).casefold().strip()
    text = re.sub(r"[^\w\s]", " ", text)

    return " ".join(text.split())


def calculate_similarity(text1, text2):

    text1 = normalise_text(text1)
    text2 = normalise_text(text2)

    if not text1 or not text2:
        return 0.0

    return SequenceMatcher(
        None,
        text1,
        text2
    ).ratio()


def find_possible_duplicates(
    new_complaint,
    existing_complaints,
    threshold=0.65
):
    possible_duplicates = []

     # Don't process an empty complaint draft.
    if not isinstance(new_complaint, dict):
        return []

    new_category = normalise_text(
        new_complaint.get("category")
    )
    """
    Find potentially similar complaints.

    This is a prototype screening mechanism.
    It does not automatically reject or merge complaints.
    """

    possible_duplicates = []

    new_category = normalise_text(
        new_complaint.get("category")
    )

    new_location = new_complaint.get("location")
    new_transcript = new_complaint.get(
        "original_transcript"
    )

    for existing in existing_complaints:

        if (
            existing.get("complaint_id")
            == new_complaint.get("complaint_id")
        ):
            continue

        existing_category = normalise_text(
            existing.get("category")
        )

        # Compare only complaints in the same category.
        if new_category != existing_category:
            continue

        transcript_score = calculate_similarity(
            new_transcript,
            existing.get("original_transcript")
        )

        location_score = calculate_similarity(
            new_location,
            existing.get("location")
        )

        combined_score = (
            transcript_score * 0.65
            + location_score * 0.35
        )

        if combined_score >= threshold:

            possible_duplicates.append({
                "complaint_id": existing.get(
                    "complaint_id"
                ),
                "category": existing.get("category"),
                "location": existing.get("location"),
                "status": existing.get("status"),
                "similarity": round(
                    combined_score * 100, 2
                ),
                "original_transcript": existing.get(
                    "original_transcript"
                )
            })

    return sorted(
        possible_duplicates,
        key=lambda item: item["similarity"],
        reverse=True
    )
