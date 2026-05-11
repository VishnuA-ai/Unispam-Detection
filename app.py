from pathlib import Path
import pickle
import re
import json
from typing import Dict
import asyncio

from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from utils.preprocess import normalize_text, extract_extra_features
from utils.security import extract_urls_from_text, check_safe_browsing, extract_text_from_image
from utils.ai_services import generate_spam_reasons

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="UniSpam AI", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Load model
with open(MODEL_DIR / "pipeline.pkl", "rb") as pf:
    pipeline = pickle.load(pf)

# Load translations
with open(BASE_DIR / "translations.json", "r", encoding="utf-8") as tf:
    TRANSLATIONS = json.load(tf)

PLATFORMS = {"email", "sms", "whatsapp", "other"}
HIGHLIGHT_TERMS = [
    "urgent", "act now", "limited time", "free", "win", "lottery", "claim",
    "click", "verify", "otp", "offer", "congratulations", "cash", "prize",
    "உடனடி", "அவசர", "வெகுமதி", "இலவச", "வெற்றி", "சரிபார்க்கவும்"
]

# Bilingual Translations
BILINGUAL_TRANSLATIONS = {
    "en": {
        "high_risk": "HIGH RISK",
        "medium_risk": "MEDIUM RISK",
        "low_risk": "LOW RISK",
        "spam_detected": "SPAM DETECTED",
        "not_spam": "NOT SPAM",
        "confidence": "Confidence",
        "error_message": "Please enter a valid message",
        "api_error": "Service error"
    },
    "ta": {
        "high_risk": "அதிக அபாயம்",
        "medium_risk": "நடுத்தர அபாயம்",
        "low_risk": "குறைந்த அபாயம்",
        "spam_detected": "ஸ்பேம் கண்டறியப்பட்டது",
        "not_spam": "ஸ்பேம் இல்லை",
        "confidence": "நம்பிக்கை",
        "error_message": "தயவுசெய்து சரியான செய்தி உள்ளிடவும்",
        "api_error": "சேவை பிழை"
    }
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _get_translation(lang: str, key: str, fallback: str = ""):
    """Get translation from translations dict"""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS.get("en", {}))
    return lang_dict.get(key, fallback)


def highlight_text(text: str, terms: list, is_tamil: bool = False) -> str:
    """Highlight suspicious terms in text"""
    highlighted = text
    safe_terms = sorted(set([t for t in terms if t]), key=len, reverse=True)
    
    for term in safe_terms:
        pattern = re.compile(rf"({re.escape(term)})", re.IGNORECASE)
        highlighted = pattern.sub(r'<mark style="background: #ffec99; padding: 2px 4px; border-radius: 4px;">\1</mark>', highlighted)
    
    return highlighted.replace("\n", "<br>")


async def hybrid_predict(message: str, platform: str, language: str = "en") -> Dict:
    """
    Hybrid spam detection using ML + rules + AI
    """
    
    # Normalize and predict
    cleaned = normalize_text(message)
    vector = [cleaned]
    model_label = pipeline.predict(vector)[0]
    probabilities = pipeline.predict_proba(vector)[0]
    
    class_index = list(pipeline.classes_).index("spam")
    ml_spam_prob = float(probabilities[class_index])
    
    # Extract URLs and check them
    urls = extract_urls_from_text(message)
    url_threats = {}
    for url in urls:
        url_threats[url] = check_safe_browsing(url)
    
    has_dangerous_links = any(not threat.get("is_safe", True) for threat in url_threats.values())
    
    # Rule-based scoring
    rule_score = _calculate_rule_score(message, platform, has_dangerous_links)
    
    # Hybrid verdict
    hybrid_score = _clamp((ml_spam_prob * 0.5) + (rule_score * 0.5), 0.0, 1.0)
    verdict = "Spam" if hybrid_score >= 0.5 or rule_score >= 0.3 else "Not Spam"
    
    # Generate AI-powered reasons
    ai_reasons = await generate_spam_reasons(message, platform, language, ml_spam_prob)
    
    # Combine reasons
    reasons = ai_reasons[:2] if isinstance(ai_reasons, list) else []
    
    confidence = hybrid_score if verdict == "Spam" else 1 - hybrid_score
    confidence = min(100, round(confidence * 100, 2))
    
    # Platform insight based on language
    platform_insight = _get_platform_insight(platform, verdict, language, has_dangerous_links)
    
    return {
        "result": verdict,
        "confidence": confidence,
        "platform": platform,
        "platform_insight": platform_insight,
        "reasons": reasons,
        "highlighted_text": highlight_text(message, HIGHLIGHT_TERMS),
        "ml_probability": round(ml_spam_prob * 100, 2),
        "rule_score": round(rule_score * 100, 2),
    }


def _calculate_rule_score(text: str, platform: str, has_dangerous_links: bool) -> float:
    """Calculate rule-based spam score"""
    score = 0.0
    lower_text = text.lower()
    
    # Dangerous links
    if has_dangerous_links:
        score += 0.3
    
    # Urgency words
    urgency_words = ["urgent", "immediately", "act now", "asap", "verify now", "உடனடி", "அவசர"]
    if any(word in lower_text for word in urgency_words):
        score += 0.15
    
    # Prize/reward words
    reward_words = ["win", "free", "congratulations", "prize", "reward", "lottery", "வெகுமதி", "வெற்றி"]
    if any(word in lower_text for word in reward_words):
        score += 0.15
    
    # Financial/sensitive words
    financial_words = ["bank", "account", "password", "credit", "refund", "loan", "வங்கி", "கடவுச்சொல்"]
    if any(word in lower_text for word in financial_words):
        score += 0.1
    
    # Excessive punctuation
    if len(re.findall(r"[!?]{2,}", text)) > 0:
        score += 0.1
    
    # Platform-specific
    if platform == "email":
        # Email-specific phishing indicators
        if any(word in lower_text for word in ["confirm account", "verify account", "click here"]):
            score += 0.1
    
    elif platform == "whatsapp":
        # WhatsApp-specific indicators
        if any(word in lower_text for word in ["forwarded", "share this", "group", "viral"]):
            score += 0.1
    
    return min(1.0, score)


def _get_platform_insight(platform: str, verdict: str, language: str, has_dangerous_links: bool) -> str:
    """Generate platform-specific insight"""
    
    if language == "ta":
        if platform == "email":
            return "மின்னஞ்சல் இணைப்புகள் மற்றும் சேகரிக்கப்பட்ட உண்மை சரிபார்க்கவும்." if verdict == "Spam" else "இது ஒரு சாதாரண மின்னஞ்சல் தோன்றுகிறது."
        elif platform == "sms":
            return "SMS இல் அசாதாரண விதவுறுப்பு வாக்கு. சந்தேகமாக பெறப்பட்ட இணைப்பு தவிர்க்கவும்." if verdict == "Spam" else "இது ஒரு சாதாரண SMS."
        elif platform == "whatsapp":
            return "WhatsApp செய்திக்கள் பெரும்பாலான ஸ்பேம் சாதாரணமாக பகிர்ந்து கொள்ளப்பட்ட இணைப்புகளாக உள்ளன." if verdict == "Spam" else "இது ஒரு சாதாரண WhatsApp செய்தி."
        else:
            return "இந்த செய்தி மற்ற தளங்களிலிருந்து ஸ்பேம் குறிகாட்டிகளைக் காட்டுகிறது." if verdict == "Spam" else "இது ஒரு சாதாரண செய்தி."
    
    else:  # English
        if platform == "email":
            return "Email links often redirect to phishing sites. Verify the sender before clicking." if verdict == "Spam" else "Looks like a normal email."
        elif platform == "sms":
            return "SMS phishing (smishing) is common. Never click links from unknown senders." if verdict == "Spam" else "Looks like a normal SMS."
        elif platform == "whatsapp":
            return "WhatsApp spam often spreads through forwarded chains and viral links." if verdict == "Spam" else "Looks like a normal WhatsApp message."
        else:
            return "This message shows spam indicators across platforms." if verdict == "Spam" else "Looks like a normal message."


# ========== ROUTES ==========

@app.get("/", response_class=HTMLResponse)
async def language_select():
    """Redirect to language selection page"""
    return FileResponse(TEMPLATES_DIR / "language-select.html")


@app.get("/index.html", response_class=HTMLResponse)
async def home(request: Request):
    """Main app page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/translations")
async def get_translations():
    """Get translations in JSON format"""
    return JSONResponse(TRANSLATIONS)


@app.post("/predict")
async def predict(
    platform: str = Form(...),
    message: str = Form(...),
    language: str = Form("en")
):
    """Main spam detection endpoint"""
    
    platform = platform.lower().strip()
    language = language.lower().strip() or "en"
    
    if platform not in PLATFORMS:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid platform selected."}
        )
    
    if not message or len(message.strip()) < 3:
        return JSONResponse(
            status_code=400,
            content={"error": _get_translation(language, "error_message")}
        )
    
    try:
        result = await hybrid_predict(message=message.strip(), platform=platform, language=language)
        return JSONResponse(result)
    except Exception as e:
        print(f"Prediction error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": _get_translation(language, "api_error")}
        )


@app.post("/ocr-scan")
async def ocr_scan(image: UploadFile = File(...), language: str = Form("en")):
    """OCR endpoint for screenshot scanning"""
    
    try:
        # Read image bytes
        image_bytes = await image.read()
        
        # Extract text using OCR
        extracted_text = await extract_text_from_image(image_bytes)
        
        return JSONResponse({
            "extracted_text": extracted_text,
            "language": language
        })
    
    except Exception as e:
        print(f"OCR error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process screenshot"}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "UniSpam AI v2.0",
        "features": ["ML Detection", "Rule Engine", "AI Reasons", "OCR Scanning", "Safe Browsing", "Bilingual"]
    }