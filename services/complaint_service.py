
from database.db import (
    initialize_database,
    save_complaint,
    get_all_complaints
)


def store_complaint(complaint):
    initialize_database()
    save_complaint(complaint)

    print(
        f"Complaint {complaint['complaint_id']} "
        "saved successfully!"
    )


def display_complaints():
    complaints = get_all_complaints()

    print("\n========== STORED COMPLAINTS ==========")

    for complaint in complaints:
        print("ID:", complaint["complaint_id"])
        print("Category:", complaint["category"])
        print("Location:", complaint["location"])
        print("Status:", complaint["status"])
        print("---------------------------------------")

    print("Total complaints:", len(complaints))


if __name__ == "__main__":
    initialize_database()
    display_complaints()
