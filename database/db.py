
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone


# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DB_PATH = Path(__file__).resolve().parent / "kural2action.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# =====================================================
# DATABASE INITIALIZATION AND MIGRATION
# =====================================================

def initialize_database():
    """
    Create the complaints table and safely add new
    geospatial columns to existing databases.
    """

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                complaint_id TEXT PRIMARY KEY,
                original_transcript TEXT NOT NULL,
                language TEXT,
                category TEXT,
                description TEXT,
                duration TEXT,
                severity TEXT,
                severity_reason TEXT,
                location TEXT,
                location_verified INTEGER DEFAULT 0,
                missing_fields TEXT,
                status TEXT,
                created_at TEXT
            )
        """)

        # Existing database migration.
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(complaints)"
            ).fetchall()
        }

        new_columns = {
            "latitude": "REAL",
            "longitude": "REAL",
            "location_source": "TEXT",
            "geocoding_confidence": "TEXT",
            "coordinates_verified": "INTEGER DEFAULT 0",
            "coordinate_updated_at": "TEXT"
        }

        for column, data_type in new_columns.items():

            if column not in existing_columns:

                connection.execute(
                    f"ALTER TABLE complaints "
                    f"ADD COLUMN {column} {data_type}"
                )

    print("Kural2Action database initialized successfully!")
    print("Geospatial database migration completed!")


# =====================================================
# SAVE NEW COMPLAINT
# =====================================================

def save_complaint(complaint):
    """Save a new complaint to SQLite."""

    with get_connection() as connection:

        try:

            connection.execute("""
                INSERT INTO complaints (
                    complaint_id,
                    original_transcript,
                    language,
                    category,
                    description,
                    duration,
                    severity,
                    severity_reason,
                    location,
                    location_verified,
                    missing_fields,
                    status,
                    created_at,
                    latitude,
                    longitude,
                    location_source,
                    geocoding_confidence,
                    coordinates_verified,
                    coordinate_updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
            """, (

                complaint["complaint_id"],
                complaint["original_transcript"],
                complaint.get("language"),
                complaint.get("category"),
                complaint.get("description"),
                complaint.get("duration"),
                complaint.get("severity"),
                complaint.get("severity_reason"),
                complaint.get("location"),

                int(
                    complaint.get("location_verified", False)
                ),

                json.dumps(
                    complaint.get("missing_fields", []),
                    ensure_ascii=False
                ),

                complaint.get("status"),
                complaint.get("created_at"),

                complaint.get("latitude"),
                complaint.get("longitude"),
                complaint.get("location_source"),
                complaint.get("geocoding_confidence"),

                int(
                    complaint.get("coordinates_verified", False)
                ),

                complaint.get("coordinate_updated_at")
            ))

        except sqlite3.IntegrityError:

            raise ValueError(
                f"Complaint {complaint['complaint_id']} already exists."
            )


# =====================================================
# UPDATE COMPLAINT COORDINATES
# =====================================================

def update_complaint_coordinates(
    complaint_id,
    latitude,
    longitude,
    location_source="manual",
    geocoding_confidence="citizen-confirmed",
    coordinates_verified=False
):
    """
    Permanently save geographic coordinates for an
    existing complaint.
    """

    if not (-90 <= latitude <= 90):
        raise ValueError("Invalid latitude.")

    if not (-180 <= longitude <= 180):
        raise ValueError("Invalid longitude.")

    updated_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE complaints
            SET
                latitude = ?,
                longitude = ?,
                location_source = ?,
                geocoding_confidence = ?,
                coordinates_verified = ?,
                coordinate_updated_at = ?
            WHERE complaint_id = ?
        """, (
            latitude,
            longitude,
            location_source,
            geocoding_confidence,
            int(coordinates_verified),
            updated_at,
            complaint_id
        ))

        if cursor.rowcount == 0:
            raise ValueError(
                f"Complaint {complaint_id} was not found."
            )

    print(
        f"Coordinates updated for complaint {complaint_id}"
    )


# =====================================================
# RETRIEVE ALL COMPLAINTS
# =====================================================

def get_all_complaints():
    """Retrieve all saved complaints."""

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT *
            FROM complaints
            ORDER BY created_at DESC
        """).fetchall()

    complaints = []

    for row in rows:

        complaint = dict(row)

        try:
            complaint["missing_fields"] = json.loads(
                complaint["missing_fields"] or "[]"
            )
        except (json.JSONDecodeError, TypeError):
            complaint["missing_fields"] = []

        complaint["location_verified"] = bool(
            complaint["location_verified"]
        )

        complaint["coordinates_verified"] = bool(
            complaint.get("coordinates_verified", 0)
        )

        complaints.append(complaint)

    return complaints


# =====================================================
# RETRIEVE ONE COMPLAINT
# =====================================================

def get_complaint_by_id(complaint_id):
    """Retrieve a single complaint by its ID."""

    with get_connection() as connection:

        row = connection.execute("""
            SELECT *
            FROM complaints
            WHERE complaint_id = ?
        """, (complaint_id,)).fetchone()

    if row is None:
        return None

    complaint = dict(row)

    try:
        complaint["missing_fields"] = json.loads(
            complaint["missing_fields"] or "[]"
        )
    except (json.JSONDecodeError, TypeError):
        complaint["missing_fields"] = []

    complaint["location_verified"] = bool(
        complaint["location_verified"]
    )

    complaint["coordinates_verified"] = bool(
        complaint.get("coordinates_verified", 0)
    )

    return complaint


# =====================================================
# DATABASE STATISTICS
# =====================================================

def get_database_statistics():

    with get_connection() as connection:

        total = connection.execute("""
            SELECT COUNT(*) FROM complaints
        """).fetchone()[0]

        mapped = connection.execute("""
            SELECT COUNT(*)
            FROM complaints
            WHERE latitude IS NOT NULL
            AND longitude IS NOT NULL
        """).fetchone()[0]

    return {
        "total_complaints": total,
        "mapped_complaints": mapped,
        "unmapped_complaints": total - mapped
    }
