
from datetime import datetime, timezone
from uuid import uuid4

from database.db import get_all_complaints, save_complaint


def create_test_duplicate():

    complaints = get_all_complaints()

    source = next(
        (
            c for c in complaints
            if c.get("category") == "Water Leakage"
        ),
        None
    )

    if source is None:
        print("No Water Leakage complaint found.")
        return

    duplicate = source.copy()

    duplicate["complaint_id"] = (
        "K2A-TEST-" + uuid4().hex[:8].upper()
    )

    duplicate["created_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    save_complaint(duplicate)

    print("\nTest duplicate created successfully!")
    print("Original ID:", source["complaint_id"])
    print("Duplicate ID:", duplicate["complaint_id"])
    print("Category:", duplicate["category"])
    print("Location:", duplicate.get("location"))


if __name__ == "__main__":
    create_test_duplicate()
