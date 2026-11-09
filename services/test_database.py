
from services.complaint_service import (
    store_complaint,
    display_complaints
)

sample_complaint = {
    "complaint_id": "K2A-DBTEST001",
    "original_transcript": "தண்ணீர் கசிவு புகார்",
    "language": "ta-IN",
    "category": "Water Leakage",
    "description": "Water leakage reported",
    "duration": "2 days",
    "severity": "Unassessed",
    "severity_reason": "Requires human review",
    "location": "Anna Nagar, near the main bus stop",
    "location_verified": True,
    "missing_fields": [],
    "status": "Ready for Verification",
    "created_at": "2026-11-08T15:00:00+00:00"
}

store_complaint(sample_complaint)

display_complaints()
