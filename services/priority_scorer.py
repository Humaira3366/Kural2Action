
def calculate_priority(complaint):
    """
    Calculate a transparent, rule-based priority score.
    Unassessed complaints are flagged for human review.
    """

    severity = str(complaint.get("severity", "")).strip().lower()
    duration = str(complaint.get("duration", "")).strip().lower()

    # Do not assign a priority when severity is unassessed.
    severity_scores = {
        "high": 50,
        "medium": 30,
        "low": 10
    }

    if severity not in severity_scores:
        return {
            "priority_score": None,
            "priority_level": "Needs Assessment",
            "priority_reason": "Severity has not been assessed."
        }

    score = severity_scores[severity]
    reasons = [f"Severity: {severity}"]

    # Add points based on how long the issue has continued.
    if "day" in duration:
        try:
            days = int(duration.split()[0])

            if days >= 7:
                score += 20
                reasons.append("Reported for 7 or more days")
            elif days >= 3:
                score += 10
                reasons.append("Reported for 3 or more days")
        except (ValueError, IndexError):
            pass

    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return {
        "priority_score": score,
        "priority_level": level,
        "priority_reason": "; ".join(reasons)
    }
