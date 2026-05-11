import re
from typing import Dict, List

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EXCESSIVE_PUNCT_PATTERN = re.compile(r"([!?$])\1{1,}")
NUMBER_CLUSTER_PATTERN = re.compile(r"\d{5,}")

URGENCY_WORDS = {"urgent", "immediately", "act now", "limited time", "now", "asap", "expire", "expires", "verify now"}
PRIZE_WORDS = {"win", "winner", "free", "lottery", "prize", "congratulations", "reward", "gift", "cash"}
FINANCIAL_WORDS = {"bank", "account", "loan", "payment", "upi", "wallet", "refund", "credit", "debit"}
OTP_WORDS = {"otp", "code", "verification code", "reset", "password", "login"}
WHATSAPP_WORDS = {"forwarded", "share this", "viral", "group", "join now"}
EMAIL_WORDS = {"invoice", "security alert", "attachment", "click below", "confirm account"}

def _find_terms(text: str, terms: set) -> List[str]:
    lower = text.lower()
    return [term for term in terms if term in lower]

def analyze_rules(text: str, platform: str) -> Dict:
    reasons = []
    signals = []
    matched_terms = []
    score = 0.0

    if URL_PATTERN.search(text):
        reasons.append("Contains a suspicious link or redirect pattern.")
        signals.append("link_detected")
        score += 0.22

    urgency_hits = _find_terms(text, URGENCY_WORDS)
    if urgency_hits:
        reasons.append("Urgency language suggests pressure-based manipulation.")
        signals.append("urgency_keywords")
        matched_terms.extend(urgency_hits)
        score += 0.18

    prize_hits = _find_terms(text, PRIZE_WORDS)
    if prize_hits:
        reasons.append("Prize or reward language matches common scam wording.")
        signals.append("prize_keywords")
        matched_terms.extend(prize_hits)
        score += 0.20

    if EXCESSIVE_PUNCT_PATTERN.search(text):
        reasons.append("Excessive punctuation increases suspicion.")
        signals.append("excessive_punctuation")
        score += 0.10

    if NUMBER_CLUSTER_PATTERN.search(text):
        reasons.append("Large numeric patterns may indicate fake contact, payment, or code bait.")
        signals.append("number_clusters")
        score += 0.10

    financial_hits = _find_terms(text, FINANCIAL_WORDS)
    otp_hits = _find_terms(text, OTP_WORDS)
    whatsapp_hits = _find_terms(text, WHATSAPP_WORDS)
    email_hits = _find_terms(text, EMAIL_WORDS)

    if platform == "sms" and (otp_hits or financial_hits):
        reasons.append("SMS content resembles OTP, banking, or payment scam patterns.")
        signals.append("sms_scam_pattern")
        matched_terms.extend(otp_hits + financial_hits)
        score += 0.15

    if platform == "email" and (email_hits or URL_PATTERN.search(text)):
        reasons.append("Email content resembles phishing or credential-harvesting behavior.")
        signals.append("email_phishing_pattern")
        matched_terms.extend(email_hits)
        score += 0.15

    if platform == "whatsapp" and (whatsapp_hits or prize_hits):
        reasons.append("WhatsApp content resembles forwarded scam or fake offer behavior.")
        signals.append("whatsapp_forward_offer_pattern")
        matched_terms.extend(whatsapp_hits)
        score += 0.15

    if platform == "other" and (urgency_hits or prize_hits or financial_hits):
        reasons.append("General text contains classic spam trigger phrases.")
        signals.append("generic_spam_language")
        matched_terms.extend(financial_hits)
        score += 0.08

    score = min(score, 1.0)
    return {
        "reasons": list(dict.fromkeys(reasons)),
        "signals": list(dict.fromkeys(signals)),
        "matched_terms": list(dict.fromkeys(matched_terms)),
        "score": score,
    }

def build_platform_insight(platform: str, rule_report: Dict, ml_spam_prob: float, verdict: str) -> str:
    if platform == "email":
        return "Looks like email phishing behavior with formal bait and link-driven risk." if verdict == "Spam" else "This reads more like a normal email than a phishing attempt."
    if platform == "sms":
        return "Looks like an SMS scam pattern, especially around urgency, OTP, or financial prompts." if verdict == "Spam" else "This does not strongly match common SMS scam structures."
    if platform == "whatsapp":
        return "Looks like a WhatsApp forward or fake-offer pattern often used in viral scam chains." if verdict == "Spam" else "This does not strongly resemble the usual WhatsApp scam-forward style."
    return "Detected using general spam heuristics across mixed text inputs." if verdict == "Spam" else "General text appears low-risk under the current hybrid checks."