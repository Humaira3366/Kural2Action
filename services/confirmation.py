
def confirm_complaint_location(complaint, citizen_confirmed):
    """
    Mark a location as verified only after citizen confirmation.
    """

    if not complaint.get("location"):
        raise ValueError("No location available to confirm.")

    if citizen_confirmed:
        complaint["location_verified"] = True
        complaint["status"] = "Ready for Verification"
        complaint["missing_fields"] = [
            field for field in complaint.get("missing_fields", [])
            if field != "location"
        ]
    else:
        complaint["location_verified"] = False
        complaint["status"] = "Pending Verification"

    return complaint


if __name__ == "__main__":
    sample_complaint = {
        "complaint_id": "K2A-TEST1234",
        "location": "Anna Nagar, near the main bus stop",
        "missing_fields": [],
        "status": "Pending Verification"
    }

    updated = confirm_complaint_location(
        sample_complaint,
        citizen_confirmed=True
    )

    print("\n========== LOCATION CONFIRMATION ==========")
    print(updated)
    print("===========================================\n")
