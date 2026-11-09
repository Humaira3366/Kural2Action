
import re
import uuid
from datetime import datetime, timezone


# ==================================================
# 1. TEXT NORMALISATION
# ==================================================

def normalise_text(text):
    if not text:
        return ""

    text = str(text).casefold()
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


# ==================================================
# 2. COMPLAINT CATEGORY KEYWORDS
# ==================================================

CATEGORY_KEYWORDS = {
    "Water Leakage": [
        "water leakage", "water leak", "leaking water",
        "pipeline leak", "pipe leakage", "burst pipe",
        "broken pipeline", "damaged pipeline",
        "drinking water leaking", "water is being wasted",
        "water is leaking",
        "தண்ணீர் கசிவு", "தண்ணி கசிவு",
        "குழாய் உடைப்பு", "குடிநீர் கசிவு",
        "குழாயில் கசிவு", "thanni kasivu",
        "water leak aaguthu"
    ],

    "Road Damage": [
        "pothole", "pot hole", "potholes",
        "road damage", "damaged road", "broken road",
        "road is damaged", "road is broken",
        "road has potholes", "road surface is damaged",
        "uneven road", "cracked road", "cracks on the road",
        "road repair", "damaged pavement",
        "crater on the road",
        "சாலை சேதம்", "சாலை பள்ளம்",
        "சாலையில் பள்ளம்", "குண்டும் குழியுமான சாலை",
        "சாலை உடைந்துள்ளது", "சாலை பழுதடைந்துள்ளது",
        "road damage aagiduchu"
    ],

    "Garbage": [
        "garbage", "waste collection", "garbage collection",
        "trash", "rubbish", "dumping waste", "waste dumping",
        "garbage accumulation", "garbage pickup",
        "uncollected garbage", "garbage has not been collected",
        "குப்பை", "குப்பைகள்", "குப்பை அகற்றப்படவில்லை",
        "குப்பை தேங்கியுள்ளது", "kuppai", "kuppai edukala"
    ],

    "Drainage": [
        "drainage", "sewage", "blocked drain",
        "drain blockage", "overflowing drain",
        "drain overflow", "drain is blocked",
        "sewage water", "sewage overflow",
        "wastewater overflow", "stormwater drain",
        "சாக்கடை", "கழிவுநீர்", "வடிகால் அடைப்பு",
        "சாக்கடை அடைப்பு", "கழிவுநீர் தேக்கம்",
        "drain block"
    ],

    "Street Lighting": [
        "street light", "streetlight", "street lights",
        "no street lights", "no lights",
        "broken street light", "street light not working",
        "street lights are not working",
        "street light is not working",
        "dark street", "poor street lighting",
        "தெருவிளக்கு", "விளக்கு எரியவில்லை",
        "தெருவிளக்கு எரியவில்லை",
        "தெருவில் வெளிச்சம் இல்லை"
    ],

    "Electricity": [
        "power cut", "power outage", "electricity",
        "no electricity", "electricity supply",
        "electricity failure", "power supply",
        "electricity is unavailable", "frequent power cuts",
        "transformer issue", "damaged electric wire",
        "மின்தடை", "மின்சாரம் இல்லை",
        "மின்சார தடை", "மின்சார கம்பி",
        "மின்சாரம் துண்டிக்கப்பட்டது"
    ]
}


# ==================================================
# 3. CATEGORY MATCHING
# ==================================================

def keyword_matches(text, keyword):
    keyword = keyword.casefold().strip()

    if not keyword:
        return False

    if re.search(r"[a-z]", keyword):
        pattern = (
            r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"
        )
        return re.search(pattern, text) is not None

    return keyword in text


def extract_category(text):
    normalized = normalise_text(text)

    if not normalized:
        return "Other"

    category_scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():

        matches = [
            keyword for keyword in keywords
            if keyword_matches(normalized, keyword)
        ]

        if matches:
            category_scores[category] = (
                sum(len(keyword.split()) for keyword in matches)
                + len(matches) * 0.5
            )

    if not category_scores:
        return "Other"

    return max(category_scores, key=category_scores.get)


# ==================================================
# 4. DURATION EXTRACTION
# ==================================================

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10
}


def extract_duration(text):
    normalized = normalise_text(text)

    numeric_patterns = [
        (r"\b(\d+)\s*days?\b", "day"),
        (r"\b(\d+)\s*hours?\b", "hour"),
        (r"\b(\d+)\s*weeks?\b", "week"),
        (r"\b(\d+)\s*months?\b", "month")
    ]

    for pattern, unit in numeric_patterns:
        match = re.search(pattern, normalized)

        if match:
            value = int(match.group(1))
            plural = "" if value == 1 else "s"
            return f"{value} {unit}{plural}"

    for word, value in NUMBER_WORDS.items():

        pattern = (
            r"\b" + word
            + r"\s+(days?|hours?|weeks?|months?)\b"
        )

        match = re.search(pattern, normalized)

        if match:
            unit = match.group(1).rstrip("s")
            plural = "" if value == 1 else "s"
            return f"{value} {unit}{plural}"

    duration_phrases = [
        (r"\bsince yesterday\b", "1 day"),
        (r"\bsince last night\b", "Since last night"),
        (r"\bsince this morning\b", "Since this morning"),
        (r"\bfor several days\b", "Several days"),
        (r"\bfor a few days\b", "A few days"),
        (r"\bfor a week\b", "1 week"),
        (r"\bfor a month\b", "1 month"),
        (r"\bfor a long time\b", "Duration unspecified")
    ]

    for pattern, result in duration_phrases:
        if re.search(pattern, normalized):
            return result

    tamil_durations = [
        (r"பத்து நாட்களாக|பத்து நாளாக", "10 days"),
        (r"ஐந்து நாட்களாக|ஐந்து நாளாக", "5 days"),
        (r"நான்கு நாட்களாக", "4 days"),
        (r"மூன்று நாட்களாக|மூன்று நாளாக", "3 days"),
        (r"இரண்டு நாட்களாக|இரண்டு நாளாக|ரெண்டு நாளாக", "2 days"),
        (r"ஒரு நாளாக|ஒரு நாளில்", "1 day")
    ]

    for pattern, result in tamil_durations:
        if re.search(pattern, normalized):
            return result

    return "Unknown"


# ==================================================
# 5. SEVERITY ASSESSMENT
# ==================================================

HIGH_URGENCY_KEYWORDS = [
    "emergency",
    "immediate danger",
    "dangerous",
    "life threatening",
    "risk of accident",
    "accident",
    "electric shock",
    "exposed electrical wire",
    "live electric wire",
    "fire",
    "injured",
    "serious injury",
    "flooding",
    "unsafe for pedestrians",
    "விபத்து",
    "ஆபத்து",
    "மின்சார கம்பி",
    "தீ விபத்து",
    "காயம்"
]

MEDIUM_URGENCY_KEYWORDS = [
    "overflow",
    "traffic congestion",
    "traffic blocked",
    "traffic disruption",
    "school",
    "hospital",
    "pedestrians",
    "children",
    "slippery road",
    "road has become slippery",
    "heavy leakage",
    "public safety",
    "பள்ளி",
    "மருத்துவமனை",
    "போக்குவரத்து தடை",
    "மக்களுக்கு பாதிப்பு"
]


def assess_severity(text):
    normalized = normalise_text(text)

    for keyword in HIGH_URGENCY_KEYWORDS:
        if keyword_matches(normalized, keyword):
            return (
                "High",
                f"Potential safety concern detected: {keyword}"
            )

    for keyword in MEDIUM_URGENCY_KEYWORDS:
        if keyword_matches(normalized, keyword):
            return (
                "Medium",
                f"Potential public-impact concern detected: {keyword}"
            )

    return (
        "Unassessed",
        "Requires further information or human review"
    )


# ==================================================
# 6. MAIN COMPLAINT EXTRACTION ENGINE
# ==================================================

def extract_complaint(transcript, language="unknown"):

    if not transcript or not str(transcript).strip():
        raise ValueError("Transcript cannot be empty")

    transcript = str(transcript).strip()

    category = extract_category(transcript)
    duration = extract_duration(transcript)

    severity, severity_reason = assess_severity(transcript)

    # Never invent a location.
    # Location must be captured and confirmed separately.
    location = None

    missing_fields = ["location"]

    if duration == "Unknown":
        missing_fields.append("duration")

    if category == "Other":
        missing_fields.append("issue_category_confirmation")

    descriptions = {
        "Water Leakage": "Water leakage or pipeline issue reported",
        "Road Damage": "Road damage or pothole reported",
        "Garbage": "Garbage accumulation or collection issue reported",
        "Drainage": "Drainage or sewage issue reported",
        "Street Lighting": "Street lighting issue reported",
        "Electricity": "Electricity-related issue reported",
        "Other": "Unclassified civic issue reported"
    }

    return {
        "complaint_id": "K2A-" + uuid.uuid4().hex[:8].upper(),
        "original_transcript": transcript,
        "language": language,
        "category": category,
        "description": descriptions[category],
        "duration": duration,
        "severity": severity,
        "severity_reason": severity_reason,
        "location": location,
        "missing_fields": missing_fields,
        "status": "Pending Verification",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
