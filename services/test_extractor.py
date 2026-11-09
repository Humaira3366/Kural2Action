
from services.complaint_extractor import extract_complaint
import json

# Actual transcript returned by Gnani Prisma
transcript = (
    "எங்கள் தெருவில் ரெண்டு நாளாக தண்ணி கசிவு "
    "இருக்குது, இதை சரி செய்ய தயவுசெய்து நடவடிக்கைஎடுங்கள்."
)

complaint = extract_complaint(
    transcript=transcript,
    language="ta-IN"
)

print("\n========== KURAL2ACTION INTELLIGENCE ==========\n")

print(json.dumps(
    complaint,
    ensure_ascii=False,
    indent=4
))

print("\n===============================================\n")
