
import time
import streamlit as st
import pandas as pd
import plotly.express as px
import folium

from folium.plugins import MarkerCluster, HeatMap
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

import os
import tempfile

from services.location_capture import transcribe_audio
from services.complaint_extractor import extract_complaint
from services.clarification import generate_clarification
from services.voice_response import generate_voice_response
from services.complaint_updater import (
    extract_location_text,
    update_complaint_location
)
from services.confirmation import confirm_complaint_location
from services.duplicate_detector import find_possible_duplicates
from services.priority_scorer import calculate_priority

from database.db import (
    get_all_complaints,
    update_complaint_coordinates,
    initialize_database,
    save_complaint
)


# ==========================================================
# 1. PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Kural2Action | Civic Intelligence",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================================
# 2. CUSTOM STYLING
# ==========================================================

st.markdown("""
<style>
    .stApp {
        background-color: #111827;
        color: #F9FAFB;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    div[data-testid="stMetric"] {
        background-color: #1F2937;
        border: 1px solid #374151;
        padding: 22px;
        border-radius: 14px;
    }

    div[data-testid="stMetricLabel"] p {
        color: #D1D5DB !important;
        font-size: 15px !important;
    }

    div[data-testid="stMetricValue"] {
        color: #60A5FA !important;
        font-size: 30px !important;
        font-weight: 700 !important;
    }

    h1, h2, h3 {
        color: #F9FAFB !important;
    }

    .stTextInput input {
        background-color: #1F2937;
        color: white;
        border: 1px solid #4B5563;
    }

    .stButton button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        border: none;
    }

    .stButton button:hover {
        background-color: #1D4ED8;
        color: white;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #374151;
        border-radius: 10px;
    }

    hr {
        border-color: #374151;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================================
# 3. DATABASE LOADING
# ==========================================================

@st.cache_data(ttl=10)
def load_complaints():
    return get_all_complaints()


def refresh_database():
    st.cache_data.clear()


if st.sidebar.button("🔄 Refresh Database"):
    refresh_database()
    st.rerun()


complaints = load_complaints()

st.title("🏙️ Kural2Action")
st.subheader("Voice-to-Action Civic Intelligence Platform")

st.caption(
    "Transforming citizen voice reports into actionable civic intelligence."
)

st.divider()


# ==========================================================
# 4. VOICE COMPLAINT REGISTRATION
# ==========================================================

st.markdown("## 🎙️ Voice Complaint Registration")
st.write(
    "Record a civic issue in your own language. Kural2Action uses "
    "Gnani Prisma to transcribe the report and Timbre to speak "
    "clarification questions."
)

language_options = {
    "Tamil": "ta-IN",
    "English": "en-IN"
}

selected_language = st.selectbox(
    "Choose your speaking language",
    list(language_options.keys()),
    key="voice_language"
)
language_code = language_options[selected_language]

# Keep the draft across Streamlit reruns.
if "voice_complaint_draft" not in st.session_state:
    st.session_state.voice_complaint_draft = None

if "voice_clarification_text" not in st.session_state:
    st.session_state.voice_clarification_text = None

if "voice_clarification_path" not in st.session_state:
    st.session_state.voice_clarification_path = None

# ----------------------------------------------------------
# STEP 1: RECORD AND TRANSCRIBE THE COMPLAINT
# ----------------------------------------------------------

st.markdown("### Step 1 — Describe the civic issue")

complaint_audio = st.audio_input(
    "Record your complaint",
    key="citizen_complaint_audio"
)

if st.button("🎧 Transcribe Complaint", type="primary"):

    if complaint_audio is None:
        st.warning("Please record your complaint before continuing.")

    else:
        temporary_audio_path = None

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            ) as temporary_audio:
                temporary_audio.write(complaint_audio.getvalue())
                temporary_audio_path = temporary_audio.name

            with st.spinner("Gnani Prisma is transcribing your complaint..."):
                transcription_result = transcribe_audio(
                    temporary_audio_path,
                    language_code=language_code
                )

            transcript = (
                transcription_result.get("transcript") or ""
            ).strip()

            if not transcript:
                st.error(
                    "No speech was detected. Please record your complaint again."
                )
            else:
                complaint = extract_complaint(
                    transcript,
                    language=language_code
                )

                st.session_state.voice_complaint_draft = complaint
                st.session_state.voice_clarification_text = None
                st.session_state.voice_clarification_path = None

                if "location" in complaint.get("missing_fields", []):
                    clarification_question = generate_clarification(
                        complaint
                    )
                    st.session_state.voice_clarification_text = (
                        clarification_question
                    )

                    try:
                        clarification_file = (
                            "samples/browser_clarification.wav"
                        )

                        with st.spinner(
                            "Gnani Timbre is generating the clarification..."
                        ):
                            generate_voice_response(
                                clarification_question,
                                language=language_code,
                                filename=clarification_file
                            )

                        st.session_state.voice_clarification_path = (
                            clarification_file
                        )

                    except Exception as tts_error:
                        st.warning(
                            "The text clarification is ready, but voice "
                            f"generation failed: {tts_error}"
                        )

                st.success("Your complaint has been transcribed.")

        except Exception as error:
            st.error(f"Complaint processing failed: {error}")

        finally:
            if (
                temporary_audio_path
                and os.path.exists(temporary_audio_path)
            ):
                os.remove(temporary_audio_path)


# ----------------------------------------------------------
# STEP 2: REVIEW THE COMPLAINT
# ----------------------------------------------------------

draft = st.session_state.voice_complaint_draft

if draft:

    st.divider()
    st.markdown("### Step 2 — Review the transcription")

    st.info(draft.get("original_transcript", ""))

    metric_one, metric_two, metric_three = st.columns(3)

    metric_one.metric(
        "Category",
        draft.get("category") or "Unknown"
    )
    metric_two.metric(
        "Duration",
        draft.get("duration") or "Unknown"
    )
    metric_three.metric(
        "Preliminary Severity",
        draft.get("severity") or "Unassessed"
    )

    st.caption(
        "Automated classification is preliminary. Severity and routing "
        "should be reviewed by an authorised human operator."
    )

    # ------------------------------------------------------
    # STEP 3: ASK FOR A LOCATION WHEN IT IS MISSING
    # ------------------------------------------------------

    if "location" in draft.get("missing_fields", []):

        st.divider()
        st.markdown("### Step 3 — Tell us where the issue is")

        clarification_question = (
            st.session_state.voice_clarification_text
            or "Please tell us your street name or a nearby landmark."
        )

        st.write("**Kural2Action asks:**")
        st.write(clarification_question)

        clarification_file = (
            st.session_state.voice_clarification_path
        )

        if (
            clarification_file
            and os.path.exists(clarification_file)
        ):
            st.audio(
                clarification_file,
                format="audio/wav"
            )

        location_audio = st.audio_input(
            "Record your street name or nearby landmark",
            key="citizen_location_audio"
        )

        if st.button("📍 Transcribe Location"):

            if location_audio is None:
                st.warning("Please record your location first.")

            else:
                temporary_location_path = None

                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".wav"
                    ) as temporary_audio:
                        temporary_audio.write(
                            location_audio.getvalue()
                        )
                        temporary_location_path = temporary_audio.name

                    with st.spinner(
                        "Gnani Prisma is transcribing your location..."
                    ):
                        location_result = transcribe_audio(
                            temporary_location_path,
                            language_code=language_code
                        )

                    location_transcript = (
                        location_result.get("transcript") or ""
                    ).strip()

                    if not location_transcript:
                        st.warning(
                            "We couldn't detect your location. "
                            "Please record it again."
                        )
                    else:
                        extracted_location = extract_location_text(
                            location_transcript
                        )

                        if not extracted_location:
                            st.warning(
                                "We couldn't extract a location phrase. "
                                "Please try again or enter it manually below."
                            )
                            st.session_state.location_transcript_for_review = (
                                location_transcript
                            )
                        else:
                            updated_draft = update_complaint_location(
                                draft,
                                extracted_location
                            )
                            st.session_state.voice_complaint_draft = (
                                updated_draft
                            )
                            st.session_state.location_transcript_for_review = (
                                location_transcript
                            )
                            st.success(
                                "Location captured. Please review it before "
                                "confirming."
                            )
                            st.rerun()

                except Exception as error:
                    st.error(f"Location processing failed: {error}")

                finally:
                    if (
                        temporary_location_path
                        and os.path.exists(temporary_location_path)
                    ):
                        os.remove(temporary_location_path)

    # ------------------------------------------------------
    # STEP 4: CITIZEN REVIEWS AND CONFIRMS THE LOCATION
    # ------------------------------------------------------

    if draft.get("location"):

        st.divider()
        st.markdown("### Step 4 — Review and confirm the location")

        location_transcript_review = st.session_state.get(
            "location_transcript_for_review"
        )

        if location_transcript_review:
            with st.expander("View the location transcription"):
                st.write(location_transcript_review)

        reviewed_location = st.text_input(
            "Extracted location (edit if needed)",
            value=draft.get("location", ""),
            key=f"review_location_{draft['complaint_id']}"
        )

        if draft.get("location_verified"):
            st.success(
                f"Citizen-confirmed location: {draft['location']}"
            )
        else:
            st.warning(
                "This location is not verified yet. Confirm it only "
                "if the displayed location is correct."
            )

            if st.button(
                "✅ Confirm This Location",
                key=f"confirm_location_{draft['complaint_id']}"
            ):

                if not reviewed_location.strip():
                    st.warning("Please enter a valid location.")
                else:
                    if reviewed_location.strip() != draft.get("location"):
                        draft = update_complaint_location(
                            draft,
                            reviewed_location.strip()
                        )

                    draft = confirm_complaint_location(
                        draft,
                        citizen_confirmed=True
                    )

                    st.session_state.voice_complaint_draft = draft
                    st.success("Location confirmed.")
                    st.rerun()

    # ------------------------------------------------------
    # STEP 5: SAVE THE COMPLAINT
    # ------------------------------------------------------

    st.divider()
    st.markdown("### Step 5 — Save the complaint")

    st.write("**Complaint ID:**", draft.get("complaint_id"))
    st.write("**Current status:**", draft.get("status"))

    if draft.get("missing_fields"):
        st.info(
            "Some information is still missing: "
            + ", ".join(draft["missing_fields"])
            + ". You can save this report as pending verification."
        )

    # ------------------------------------------------------
    # DUPLICATE DETECTION
    # ------------------------------------------------------

    existing_complaints = get_all_complaints()

    possible_duplicates = find_possible_duplicates(
        draft,
        existing_complaints
    )

    if possible_duplicates:
        st.warning(
            "⚠️ Similar complaints were found. "
            "Please review them before submitting."
        )

        for complaint in possible_duplicates:
            with st.expander(
                f"{complaint['complaint_id']} — "
                f"{complaint['similarity']}% similarity"
            ):
                st.write("Category:", complaint.get("category"))
                st.write("Location:", complaint.get("location"))
                st.write("Status:", complaint.get("status"))
                st.write("Original report:")
                st.write(complaint.get("original_transcript", ""))

        duplicate_reviewed = st.checkbox(
            "I have reviewed these possible duplicates and "
            "still want to submit this complaint.",
            key=f"voice_duplicate_reviewed_{draft.get('complaint_id', 'unknown')}"
        )
    else:
        st.success("No similar complaints detected.")
        duplicate_reviewed = True

    # The save button is available in both cases:
    # no duplicates, or duplicates explicitly reviewed.
    if st.button(
        "💾 Save Complaint to Database",
        type="primary",
        key="save_voice_complaint",
        disabled=not duplicate_reviewed
    ):
        try:
            initialize_database()
            save_complaint(draft)

            st.success(
                f"Complaint {draft.get('complaint_id')} saved successfully!"
            )

            st.session_state.voice_complaint_draft = None
            st.session_state.voice_clarification_text = None
            st.session_state.voice_clarification_path = None
            st.session_state.pop(
                "location_transcript_for_review",
                None
            )

            st.cache_data.clear()
            st.rerun()

        except Exception as error:
            st.error(
                "The complaint could not be saved. "
                f"Details: {error}"
            )

st.divider()



if not complaints:
    st.info("No complaints have been registered yet.")
    st.stop()


df = pd.DataFrame(complaints)


# Ensure expected fields exist.
required_columns = [
    "complaint_id",
    "original_transcript",
    "language",
    "category",
    "description",
    "duration",
    "severity",
    "severity_reason",
    "location",
    "location_verified",
    "missing_fields",
    "status",
    "created_at",
    "latitude",
    "longitude",
    "location_source",
    "geocoding_confidence",
    "coordinates_verified",
    "coordinate_updated_at"
]

for column in required_columns:
    if column not in df.columns:
        df[column] = None


# Clean text fields.
text_columns = [
    "complaint_id",
    "language",
    "category",
    "description",
    "duration",
    "severity",
    "location",
    "status"
]

for column in text_columns:
    df[column] = df[column].fillna("Unknown").astype(str)


# Convert coordinate fields to numeric values.
df["latitude"] = pd.to_numeric(
    df["latitude"], errors="coerce"
)

df["longitude"] = pd.to_numeric(
    df["longitude"], errors="coerce"
)

df["location_verified"] = (
    df["location_verified"].fillna(0).astype(bool)
)

df["coordinates_verified"] = (
    df["coordinates_verified"].fillna(0).astype(bool)
)


# ==========================================================
# 5. SIDEBAR FILTERS
# ==========================================================

st.sidebar.title("🎛️ Dashboard Controls")
st.sidebar.markdown("### Filter Complaints")

categories = sorted(df["category"].unique().tolist())
severities = sorted(df["severity"].unique().tolist())
statuses = sorted(df["status"].unique().tolist())
languages = sorted(df["language"].unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Complaint Category",
    categories,
    default=categories
)

selected_severities = st.sidebar.multiselect(
    "Severity",
    severities,
    default=severities
)

selected_statuses = st.sidebar.multiselect(
    "Complaint Status",
    statuses,
    default=statuses
)

selected_languages = st.sidebar.multiselect(
    "Language",
    languages,
    default=languages
)

verification_filter = st.sidebar.selectbox(
    "Location Confirmation",
    ["All", "Confirmed", "Not Confirmed"]
)


filtered_df = df[
    df["category"].isin(selected_categories)
    & df["severity"].isin(selected_severities)
    & df["status"].isin(selected_statuses)
    & df["language"].isin(selected_languages)
].copy()


if verification_filter == "Confirmed":
    filtered_df = filtered_df[
        filtered_df["location_verified"]
    ]

elif verification_filter == "Not Confirmed":
    filtered_df = filtered_df[
        ~filtered_df["location_verified"]
    ]


# ==========================================================
# 6. KPI METRICS
# ==========================================================

st.markdown("## 📊 Complaint Overview")

total = len(filtered_df)

pending = filtered_df["status"].isin([
    "Pending Verification",
    "Ready for Verification"
]).sum()

verified = filtered_df["location_verified"].sum()

high_severity = (
    filtered_df["severity"] == "High"
).sum()

unassessed = (
    filtered_df["severity"] == "Unassessed"
).sum()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Complaints", total)
c2.metric("Pending Reports", int(pending))
c3.metric("Location Confirmed", int(verified))
c4.metric("High Severity", int(high_severity))

st.caption(
    f"{int(unassessed)} complaints require severity assessment."
)

st.divider()


# ==========================================================
# 7. COMPLAINT ANALYTICS
# ==========================================================

st.markdown("## 📈 Complaint Analytics")

if filtered_df.empty:

    st.info("No complaints match your selected filters.")

else:

    left, right = st.columns(2)

    with left:

        category_counts = (
            filtered_df["category"]
            .value_counts()
            .rename_axis("Category")
            .reset_index(name="Complaints")
        )

        fig_category = px.bar(
            category_counts,
            x="Category",
            y="Complaints",
            color="Category",
            text="Complaints",
            title="Complaints by Category",
            template="plotly_dark"
        )

        fig_category.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font_color="#F9FAFB"
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

    with right:

        status_counts = (
            filtered_df["status"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Complaints")
        )

        fig_status = px.pie(
            status_counts,
            names="Status",
            values="Complaints",
            hole=0.55,
            title="Complaint Status Distribution",
            template="plotly_dark"
        )

        fig_status.update_layout(
            paper_bgcolor="#111827",
            font_color="#F9FAFB"
        )

        st.plotly_chart(
            fig_status,
            use_container_width=True
        )

    severity_counts = (
        filtered_df["severity"]
        .value_counts()
        .rename_axis("Severity")
        .reset_index(name="Complaints")
    )

    fig_severity = px.bar(
        severity_counts,
        x="Severity",
        y="Complaints",
        color="Severity",
        text="Complaints",
        title="Complaint Severity Distribution",
        template="plotly_dark"
    )

    fig_severity.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font_color="#F9FAFB"
    )

    st.plotly_chart(
        fig_severity,
        use_container_width=True
    )


# ==========================================================
# 8. GEOCODING ENGINE
# ==========================================================

st.divider()

st.markdown("## 🗺️ Geospatial Civic Intelligence")

st.write(
    "Resolve citizen-provided locations into geographic coordinates "
    "and persist them in the Kural2Action database."
)


@st.cache_data(ttl=86400)
def geocode_location(location):

    if not location or location == "Unknown":
        return None

    geolocator = Nominatim(
        user_agent="kural2action_civic_dashboard_v3"
    )

    queries = [
        f"{location}, Chennai, Tamil Nadu, India"
    ]

    # Tamil neighbourhood fallback.
    if "அண்ணா நகர்" in location:
        queries.append(
            "Anna Nagar, Chennai, Tamil Nadu, India"
        )

    for index, query in enumerate(queries):

        try:

            result = geolocator.geocode(
                query,
                timeout=20,
                exactly_one=True
            )

            if result:

                # The neighbourhood fallback is not
                # an exact incident location.
                confidence = (
                    "neighbourhood-approximate"
                    if index > 0
                    else "address-match-unverified"
                )

                return {
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "display_address": result.address,
                    "confidence": confidence
                }

        except Exception:
            pass

        if index < len(queries) - 1:
            time.sleep(1.1)

    return None


# ==========================================================
# 9. AUTOMATIC GEOCODING AND PERMANENT STORAGE
# ==========================================================

st.markdown("### 📍 Automatic Location Resolution")

unmapped_locations = filtered_df[
    filtered_df["latitude"].isna()
    | filtered_df["longitude"].isna()
]

unique_locations = [
    location
    for location in unmapped_locations["location"].unique().tolist()
    if location != "Unknown"
]

st.write(
    f"Locations awaiting geocoding: **{len(unique_locations)}**"
)


if st.button("🌍 Resolve and Save Locations"):

    progress = st.progress(0)
    message = st.empty()

    errors = []

    for index, location in enumerate(unique_locations):

        message.write(f"Resolving: {location}")

        result = geocode_location(location)

        if result:

            matching_complaints = filtered_df[
                filtered_df["location"] == location
            ]

            for _, complaint in matching_complaints.iterrows():

                try:

                    update_complaint_coordinates(
                        complaint_id=complaint["complaint_id"],
                        latitude=result["latitude"],
                        longitude=result["longitude"],
                        location_source="nominatim",
                        geocoding_confidence=result["confidence"],
                        coordinates_verified=False
                    )

                except Exception as error:
                    errors.append(
                        f"{complaint['complaint_id']}: {error}"
                    )

        progress.progress(
            (index + 1) / max(len(unique_locations), 1)
        )

        if index < len(unique_locations) - 1:
            time.sleep(1.1)

    st.cache_data.clear()

    if errors:
        st.warning("Some coordinate updates failed.")
        for error in errors:
            st.write(error)
    else:
        st.success(
            "Location lookup and database updates completed!"
        )

    st.rerun()


# ==========================================================
# 10. MANUAL MAP PIN SELECTION
# ==========================================================

st.markdown("### 📌 Manual Location Selection")

st.write(
    "When automatic geocoding cannot identify an exact location, "
    "select a map pin and save it after confirming the location."
)

complaint_options = filtered_df[
    ["complaint_id", "location"]
].drop_duplicates()

if not complaint_options.empty:

    selected_complaint = st.selectbox(
        "Select a complaint",
        complaint_options["complaint_id"].tolist(),
        key="manual_complaint_selection"
    )

    selected_row = filtered_df[
        filtered_df["complaint_id"] == selected_complaint
    ].iloc[0]

    existing_lat = selected_row["latitude"]
    existing_lon = selected_row["longitude"]

    if pd.notna(existing_lat) and pd.notna(existing_lon):

        map_center = [existing_lat, existing_lon]
        map_zoom = 15

    else:

        # Initial map view only, not an incident location.
        map_center = [13.0827, 80.2707]
        map_zoom = 11

    picker_map = folium.Map(
        location=map_center,
        zoom_start=map_zoom,
        tiles="OpenStreetMap"
    )

    if pd.notna(existing_lat) and pd.notna(existing_lon):

        folium.Marker(
            [existing_lat, existing_lon],
            tooltip="Currently saved coordinates",
            icon=folium.Icon(color="blue")
        ).add_to(picker_map)

    picker_map.add_child(
        folium.LatLngPopup()
    )

    st.caption(
        "Click the map to inspect the selected latitude and longitude."
    )

    picker_result = st_folium(
        picker_map,
        height=400,
        use_container_width=True,
        key="manual_location_picker"
    )

    clicked = (
        picker_result.get("last_clicked")
        if picker_result
        else None
    )

    if clicked:

        selected_lat = float(clicked["lat"])
        selected_lon = float(clicked["lng"])

        st.write(
            f"Selected latitude: **{selected_lat:.6f}**"
        )

        st.write(
            f"Selected longitude: **{selected_lon:.6f}**"
        )

        citizen_confirmed = st.checkbox(
            "I confirm this pin represents the reported incident location.",
            key=f"confirm_pin_{selected_complaint}"
        )

        if st.button(
            "💾 Save Coordinates Permanently",
            key=f"save_pin_{selected_complaint}"
        ):

            if not citizen_confirmed:

                st.warning(
                    "Please confirm the selected location before saving."
                )

            else:

                try:

                    update_complaint_coordinates(
                        complaint_id=selected_complaint,
                        latitude=selected_lat,
                        longitude=selected_lon,
                        location_source="manual-map-pin",
                        geocoding_confidence="citizen-confirmed",
                        coordinates_verified=True
                    )

                    st.cache_data.clear()

                    st.success(
                        f"Coordinates permanently saved for "
                        f"{selected_complaint}!"
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"Could not save coordinates: {error}"
                    )


# ==========================================================
# 11. GEOSPATIAL DATAFRAME
# ==========================================================

# Reload from SQLite so the map always uses persisted data.
@st.cache_data(ttl=10)
def load_complaints_for_map():
    return get_all_complaints()


map_records = load_complaints_for_map()

map_df = pd.DataFrame(map_records)

if not map_df.empty:

    map_df["latitude"] = pd.to_numeric(
        map_df["latitude"], errors="coerce"
    )

    map_df["longitude"] = pd.to_numeric(
        map_df["longitude"], errors="coerce"
    )

    # Apply the same sidebar filters.
    map_df = map_df[
        map_df["category"].isin(selected_categories)
        & map_df["severity"].isin(selected_severities)
        & map_df["status"].isin(selected_statuses)
        & map_df["language"].isin(selected_languages)
    ].copy()

    if verification_filter == "Confirmed":
        map_df = map_df[
            map_df["location_verified"].astype(bool)
        ]

    elif verification_filter == "Not Confirmed":
        map_df = map_df[
            ~map_df["location_verified"].astype(bool)
        ]

    mapped_df = map_df.dropna(
        subset=["latitude", "longitude"]
    ).copy()

else:

    mapped_df = pd.DataFrame()


unmapped_count = len(map_df) - len(mapped_df)

m1, m2 = st.columns(2)

m1.metric(
    "Locations with Coordinates",
    len(mapped_df)
)

m2.metric(
    "Locations Not Resolved",
    unmapped_count
)


# ==========================================================
# 12. INTERACTIVE COMPLAINT MAP
# ==========================================================

st.markdown("### 🌍 Interactive Complaint Map")

if mapped_df.empty:

    st.warning(
        "No permanent complaint coordinates are available yet. "
        "Use automatic geocoding or manually select a map pin."
    )

else:

    center_lat = mapped_df["latitude"].mean()
    center_lon = mapped_df["longitude"].mean()

    civic_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="OpenStreetMap"
    )

    marker_cluster = MarkerCluster().add_to(civic_map)

    severity_colors = {
        "High": "red",
        "Medium": "orange",
        "Low": "green",
        "Unassessed": "blue"
    }

    for _, row in mapped_df.iterrows():

        color = severity_colors.get(
            row.get("severity", "Unassessed"),
            "gray"
        )

        coordinate_source = (
            row.get("location_source") or "Unknown"
        )

        confidence = (
            row.get("geocoding_confidence") or "Unknown"
        )

        popup_html = f"""
        <div style="width:260px">
            <h4>{row['complaint_id']}</h4>
            <b>Category:</b> {row['category']}<br>
            <b>Severity:</b> {row['severity']}<br>
            <b>Status:</b> {row['status']}<br>
            <b>Location:</b> {row['location']}<br>
            <b>Source:</b> {coordinate_source}<br>
            <b>Confidence:</b> {confidence}<br>
            <b>Coordinates verified:</b>
            {bool(row.get('coordinates_verified', False))}
        </div>
        """

        folium.Marker(
            location=[
                row["latitude"],
                row["longitude"]
            ],
            popup=folium.Popup(
                popup_html,
                max_width=320
            ),
            tooltip=row["complaint_id"],
            icon=folium.Icon(
                color=color,
                icon="info-sign"
            )
        ).add_to(marker_cluster)

    st_folium(
        civic_map,
        height=550,
        use_container_width=True,
        key="kural2action_main_map"
    )

    st.caption(
        "Markers show stored coordinates. Approximate and "
        "citizen-confirmed locations are identified separately."
    )


# ==========================================================
# 13. COMPLAINT DENSITY HEATMAP
# ==========================================================

st.markdown("### 🔥 Complaint Density Heatmap")

if not mapped_df.empty:

    heat_map = folium.Map(
        location=[
            mapped_df["latitude"].mean(),
            mapped_df["longitude"].mean()
        ],
        zoom_start=12,
        tiles="OpenStreetMap"
    )

    heat_data = mapped_df[
        ["latitude", "longitude"]
    ].values.tolist()

    HeatMap(
        heat_data,
        radius=25,
        blur=18,
        min_opacity=0.35
    ).add_to(heat_map)

    st_folium(
        heat_map,
        height=450,
        use_container_width=True,
        key="kural2action_heatmap"
    )

    st.caption(
        "Heat intensity represents mapped complaint counts, "
        "not a statistically validated civic risk score."
    )

else:

    st.info(
        "The heatmap will appear once permanent complaint "
        "coordinates are available."
    )


# ==========================================================
# 14. GEOGRAPHIC SUMMARY
# ==========================================================

st.markdown("### 📍 Geographic Summary")

if not mapped_df.empty:

    geographic_summary = (
        mapped_df.groupby("location")
        .agg(
            Complaint_Count=("complaint_id", "count"),
            Verified_Coordinates=(
                "coordinates_verified",
                "sum"
            )
        )
        .reset_index()
        .sort_values(
            "Complaint_Count",
            ascending=False
        )
    )

    st.dataframe(
        geographic_summary,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "Geographic summaries will be available after locations "
        "are stored in the database."
    )


# ==========================================================
# DUPLICATE REPORTS ANALYSIS
# ==========================================================

st.divider()
st.markdown("## 🔎 Duplicate Reports Analysis")

st.write(
    "Identify potentially repeated complaints using category "
    "and text similarity. All matches require human review."
)

all_complaints = get_all_complaints()

duplicate_pairs = []
seen_pairs = set()

for complaint in all_complaints:

    matches = find_possible_duplicates(
        complaint,
        all_complaints
    )

    for match in matches:

        first_id = complaint["complaint_id"]
        second_id = match["complaint_id"]

        # Avoid displaying the same pair twice.
        pair_key = tuple(sorted([first_id, second_id]))

        if pair_key in seen_pairs:
            continue

        seen_pairs.add(pair_key)

        duplicate_pairs.append({
            "Complaint 1": first_id,
            "Complaint 2": second_id,
            "Category": complaint.get("category"),
            "Location 1": complaint.get("location"),
            "Location 2": match.get("location"),
            "Similarity (%)": match.get("similarity")
        })


if duplicate_pairs:

    duplicate_df = pd.DataFrame(duplicate_pairs)

    st.metric(
        "Potential Duplicate Pairs",
        len(duplicate_df)
    )

    st.dataframe(
        duplicate_df,
        use_container_width=True,
        hide_index=True
    )

    st.warning(
        "These are potential matches, not confirmed duplicates. "
        "Review the original reports before taking action."
    )

else:

    st.success(
        "No potential duplicate pairs detected."
    )



# ==========================================================
# 15. COMPLAINT MANAGEMENT
# ==========================================================

st.divider()

st.markdown("## 📋 Complaint Management")

search = st.text_input(
    "Search complaint ID, category or location"
)

table_df = filtered_df.copy()

# Calculate priority for each complaint
priority_results = table_df.apply(
    lambda row: calculate_priority(row.to_dict()),
    axis=1
)

table_df["priority_score"] = [
    result["priority_score"] for result in priority_results
]

table_df["priority_level"] = [
    result["priority_level"] for result in priority_results
]

if search:

    search_mask = (
        table_df["complaint_id"].str.contains(
            search, case=False, na=False
        )
        | table_df["category"].str.contains(
            search, case=False, na=False
        )
        | table_df["location"].str.contains(
            search, case=False, na=False
        )
    )

    table_df = table_df[search_mask]


display_columns = [
    "complaint_id",
    "category",
    "duration",
    "severity",
    "priority_score",
    "priority_level",
    "location",
    "location_verified",
    "status",
    "latitude",
    "longitude",
    "location_source"
]

st.dataframe(
    table_df[display_columns],
    use_container_width=True,
    hide_index=True
)


# ==========================================================
# 16. INDIVIDUAL COMPLAINT DETAILS
# ==========================================================

st.divider()

st.markdown("## 🔍 Individual Complaint Details")

if not filtered_df.empty:

    selected_id = st.selectbox(
        "Select a complaint to view details",
        filtered_df["complaint_id"].tolist()
    )

    selected = filtered_df[
        filtered_df["complaint_id"] == selected_id
    ].iloc[0]

    left, right = st.columns(2)

    with left:

        st.markdown("### Complaint Information")

        st.write("**ID:**", selected["complaint_id"])
        st.write("**Category:**", selected["category"])
        st.write("**Description:**", selected["description"])
        st.write("**Duration:**", selected["duration"])
        st.write("**Severity:**", selected["severity"])
        st.write("**Language:**", selected["language"])

    with right:

        st.markdown("### Location Information")

        st.write("**Location:**", selected["location"])

        st.write(
            "**Citizen location confirmation:**",
            "Yes" if selected["location_verified"] else "No"
        )

        st.write("**Status:**", selected["status"])

        if pd.notna(selected["latitude"]):

            st.write(
                "**Latitude:**",
                selected["latitude"]
            )

            st.write(
                "**Longitude:**",
                selected["longitude"]
            )

            st.write(
                "**Coordinate source:**",
                selected["location_source"]
            )

            st.write(
                "**Coordinate confidence:**",
                selected["geocoding_confidence"]
            )

            st.write(
                "**Coordinates verified:**",
                "Yes" if selected["coordinates_verified"] else "No"
            )

        else:

            st.info("Coordinates have not been saved yet.")

    st.markdown("### Original Citizen Transcript")

    st.info(selected["original_transcript"])

else:

    st.info("No complaints match your selected filters.")


# ==========================================================
# 17. FOOTER
# ==========================================================

st.divider()

st.caption(
    "Kural2Action | Civic Intelligence | "
    "Powered by Gnani Prisma and Timbre"
)

st.caption(
    "Geocoded coordinates are approximate until verified. "
    "Reports are locally stored and are not official municipal submissions."
)

if st.button("🔄 Refresh Dashboard"):

    st.cache_data.clear()
    st.rerun()
