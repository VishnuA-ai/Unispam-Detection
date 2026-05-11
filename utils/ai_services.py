"""
AI Services: Gemini 1.5 Flash for spam reasons generation
"""
import google.generativeai as genai
import os
import json


def configure_gemini():
    """Configure Gemini AI with API key from environment"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # For now, provide instructions for setup
        print("⚠️  Warning: GEMINI_API_KEY not set. Set it with: export GEMINI_API_KEY=your_key")
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Failed to configure Gemini: {e}")
        return False


async def generate_spam_reasons(message: str, platform: str, language: str = "en", ml_score: float = 0.0) -> list:
    """
    Generate AI-powered spam reasons using Gemini 1.5 Flash (free tier)
    
    Args:
        message: The message to analyze
        platform: Platform (email, sms, whatsapp, other)
        language: Language code (en, ta)
        ml_score: ML model's spam probability (0-1)
    
    Returns:
        List of reasons why the message is flagged
    """
    
    prompt_template_en = f"""Analyze this {platform} message and provide 2-3 concise reasons why it might be spam or phishing:

Message: "{message}"

ML Score: {ml_score * 100:.1f}%

Provide reasons in a JSON array format like: ["reason1", "reason2", "reason3"]
Be specific about what makes it suspicious (urgency, links, money requests, etc).
Return ONLY the JSON array, no other text."""

    prompt_template_ta = f"""இந்த {platform} செய்தியை பகுப்பாய்வு செய்து, இது ஸ்பேம் அல்லது ஃபிஷிங் ஏன் இருக்கக்கூடும் என்பதற்கான 2-3 கச்சிதமான காரணங்களை வழங்கவும்:

செய்தி: "{message}"

ML மதிப்பெண்: {ml_score * 100:.1f}%

குறிப்பு: ["reason1", "reason2", "reason3"] போன்ற JSON வரிசை வடிவத்தில் காரணங்களை வழங்கவும்
குறிப்பாக, அவசர நிலை, இணைப்புகள், பணம் கோரிக்கை போன்ற அதை சந்தேகமாக்குவது குறிப்பிடவும்.
கூடுதல் உரை இல்லாமல் ONLY JSON வரிசை மட்டுமே return செய்யவும்."""

    prompt = prompt_template_ta if language == "ta" else prompt_template_en

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = await _call_gemini_async(model, prompt)
        
        # Parse JSON from response
        reasons = json.loads(response.strip())
        return reasons if isinstance(reasons, list) else [response]
    
    except Exception as e:
        print(f"Gemini error: {e}")
        # Fallback to rule-based reasons
        return _fallback_reasons(message, language)


async def _call_gemini_async(model, prompt):
    """Async wrapper for Gemini API call"""
    # Since Gemini SDK is sync, we run it in thread pool
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: model.generate_content(prompt).text)


def _fallback_reasons(message: str, language: str = "en") -> list:
    """Fallback reasons when Gemini is unavailable"""
    lower_msg = message.lower()
    
    reasons_en = []
    reasons_ta = []
    
    if any(word in lower_msg for word in ["urgent", "immediately", "act now", "asap"]):
        reasons_en.append("Contains urgency or pressure language")
        reasons_ta.append("அவசர தன்மை அல்லது அழுத்தம் மொழி இருக்கிறது")
    
    if any(word in lower_msg for word in ["verify", "confirm", "password", "otp"]):
        reasons_en.append("Requests sensitive information or credentials")
        reasons_ta.append("உணர்வுশীல் தகவல் அல்லது சான்றுகளை கோருகிறது")
    
    if any(word in lower_msg for word in ["free", "win", "congratulations", "prize"]):
        reasons_en.append("Suspicious prize or reward offer")
        reasons_ta.append("சந்தேகத்திற்குரிய பரிசு அல்லது வெகுமதி வாக்கு")
    
    if "http" in lower_msg or "www" in lower_msg:
        reasons_en.append("Contains suspicious external link")
        reasons_ta.append("சந்தேகத்திற்குரிய வெளிப்புற இணைப்பு இருக்கிறது")
    
    if not reasons_en:
        reasons_en.append("Detected as potential spam by ML model")
        reasons_ta.append("ML மாதிரியால் சாத்தியமான ஸ்பேமாக கண்டறியப்பட்டது")
    
    return reasons_ta if language == "ta" else reasons_en
