# Kural2Action 🏙️
### Turning citizen voices into actionable civic intelligence

Kural2Action is a voice-first civic complaint intake and monitoring prototype. It helps citizens report everyday public-service issues in **Tamil or English**, then turns those reports into structured records that can be reviewed, prioritised and explored through a dashboard.

The goal is simple: make civic issue reporting more accessible while helping teams organise incoming complaints and identify patterns that may need attention.

---

## Why Kural2Action?

Reporting a civic issue can be difficult when a person has to navigate a lengthy form, describe the issue in a particular format, or provide every detail at once. Important information—especially the exact location—may be missing from an initial report.

Kural2Action explores a more conversational workflow: a citizen describes the issue by voice, the system extracts the available details, and it asks a follow-up question when key information is missing. The citizen can review and confirm the location before the complaint moves forward.

## What it does

- **Voice-based reporting:** Record a complaint directly in the Streamlit interface.
- **Tamil and English input:** Select Tamil (`ta-IN`) or English (`en-IN`) for speech transcription.
- **Speech-to-text:** Uses **Gnani Prisma** to convert the citizen's audio into text.
- **Complaint extraction:** Identifies a likely issue category, reported duration and preliminary severity from the transcript.
- **Contextual clarification:** Prompts for missing information, such as a street name or nearby landmark.
- **Voice responses:** Uses **Gnani Timbre** to generate spoken clarification prompts.
- **Citizen confirmation:** Keeps location verification explicit instead of silently assuming an extracted location is correct.
- **Duplicate screening:** Compares a new complaint with existing complaints in the same category and surfaces possible matches for review.
- **Priority support:** Calculates a transparent, rule-based priority score using the available severity and duration information.
- **Civic dashboard:** Presents complaint records and geographic views, including map markers and a heatmap when coordinate data is available.
- **Persistent storage:** Stores complaint records in a local SQLite database.

## How the workflow works

1. **Record** — A citizen describes a civic issue in Tamil or English.
2. **Transcribe** — Gnani Prisma converts the audio into a transcript.
3. **Structure** — Kural2Action extracts the category, duration and preliminary severity.
4. **Clarify** — If location details are missing, the system asks a follow-up question and can speak it using Gnani Timbre.
5. **Capture and confirm** — The citizen provides a location and is asked to confirm it.
6. **Check and prioritise** — The system screens for similar complaints and calculates a rule-based priority where sufficient information is available.
7. **Store and explore** — The complaint is saved to SQLite and made available to the dashboard.

## Technology

| Area | Tools |
|---|---|
| Application interface | Streamlit |
| Speech recognition | Gnani Prisma API |
| Text-to-speech | Gnani Timbre API |
| Data processing | Python, Pandas |
| Visualisation | Plotly |
| Maps and geospatial display | Folium, Streamlit-Folium, Geopy |
| Database | SQLite |
| API and configuration | Requests, python-dotenv |

## Project structure

```text
Kural2Action/
├── app2.py                     # Streamlit application and dashboard
├── main.py                     # Command-line workflow prototype
├── create_test_duplicate.py    # Duplicate-complaint test data helper
├── database/
│   └── db.py                   # SQLite setup and complaint persistence
├── services/
│   ├── location_capture.py     # Gnani Prisma speech transcription
│   ├── complaint_extractor.py  # Category, duration and severity extraction
│   ├── clarification.py        # Follow-up question generation
│   ├── voice_response.py      # Gnani Timbre text-to-speech
│   ├── complaint_updater.py   # Location capture and complaint updates
│   ├── confirmation.py        # Citizen location confirmation
│   ├── duplicate_detector.py # Similarity-based duplicate screening
│   └── priority_scorer.py    # Rule-based priority calculation
└── samples/                    # Sample audio and generated audio files
```

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/Humaira3366/Kural2Action.git
cd Kural2Action
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install streamlit pandas plotly folium geopy streamlit-folium requests python-dotenv
```

### 4. Configure Gnani API access

Create a `.env` file in the project root:

```env
GNANI_API_KEY=your_gnani_api_key
GNANI_BASE_URL=https://api.vachana.ai
```

Replace the placeholder with your own API key. Keep `.env` private: **never commit API keys or credentials to GitHub**.

### 5. Run the application

```bash
streamlit run app2.py
```

Streamlit will print a local URL in the terminal. Open that URL in your browser.

> The application requires valid Gnani API access for speech transcription and voice generation. The SQLite database is created locally by the application when initialised.

## Duplicate complaint screening

Kural2Action includes a lightweight duplicate-screening mechanism. It:

- Compares complaints within the same detected category.
- Measures text similarity between the original complaint transcripts.
- Considers location similarity when location details are available.
- Returns possible matches with a similarity percentage for review.

The current implementation uses text similarity rather than semantic embeddings. A match is a **possible duplicate**, not proof that two reports describe the same incident. Complaints are not automatically rejected or merged.

## Priority and verification

Priority scoring is currently rule-based. It uses the extracted severity and, when available, the reported duration. If severity has not been assessed, the system returns **Needs Assessment** rather than inventing a score.

Automated category and severity results are preliminary. Location confirmation and appropriate human review remain important before operational decisions are made.

## Current scope and limitations

Kural2Action is a prototype intended to demonstrate a voice-first civic reporting workflow.

- The current interface offers Tamil and English language selection.
- Category extraction relies on a maintained keyword dictionary.
- Severity assessment and priority scoring use transparent rules, not a trained predictive model.
- Duplicate screening is similarity-based and may produce false positives or miss differently worded reports.
- Map visualisations depend on usable geographic coordinates.
- The project is not yet an integrated deployment with municipal complaint-management systems.

These limitations are part of the next development opportunities: broader language coverage, stronger multilingual and semantic matching, improved geocoding, evaluation with real-world data, and integration with civic service workflows.

## Responsible use

Citizen reports can contain personal or location information. Use test or appropriately consented data during development, protect API credentials, and apply suitable access, retention and privacy controls before any real-world deployment. Automated classifications and priority scores should support—not replace—human review.

## Contributing

Suggestions, bug reports and improvements are welcome. For substantial changes, open an issue first to discuss the proposed update.

---

**Kural2Action — Listen to citizens. Understand the issue. Support civic action.**
