"""
Security Services: OCR.Space API and Google Safe Browsing API
"""
import aiohttp
import os
import requests
from typing import Dict, List


async def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image using OCR.Space API (free tier)
    
    Args:
        image_bytes: Image file bytes
    
    Returns:
        Extracted text from the image
    """
    
    ocr_space_url = "https://api.ocr.space/parse/image"
    
    # OCR.Space free API key (free tier allows 25 requests/day)
    api_key = "K87899142C88"  # Free demo key
    
    try:
        async with aiohttp.ClientSession() as session:
            files = {
                'filename': ('image.jpg', image_bytes),
            }
            
            data = {
                'apikey': api_key,
                'language': 'eng',
            }
            
            async with session.post(ocr_space_url, data=data, files=files) as response:
                result = await response.json()
                
                if result.get('IsErroredOnProcessing'):
                    return f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}"
                
                return result.get('ParsedText', '').strip()
    
    except Exception as e:
        print(f"OCR.Space API error: {e}")
        return f"Failed to extract text: {str(e)}"


def check_safe_browsing(url: str) -> Dict:
    """
    Check URL safety using Google Safe Browsing API (free tier)
    Requires Google API key set in environment: GOOGLE_SAFE_BROWSING_API_KEY
    
    Args:
        url: URL to check
    
    Returns:
        Dictionary with threat info
    """
    
    api_key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")
    
    if not api_key:
        return {
            "is_safe": True,
            "threats": [],
            "warning": "Safe Browsing API key not configured"
        }
    
    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    
    body = {
        "client": {
            "clientId": "unispam-ai",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION"
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    
    try:
        response = requests.post(endpoint, json=body, timeout=5)
        result = response.json()
        
        matches = result.get('matches', [])
        
        return {
            "is_safe": len(matches) == 0,
            "threats": [m.get('threatType', 'UNKNOWN') for m in matches],
            "warning": None
        }
    
    except Exception as e:
        print(f"Safe Browsing API error: {e}")
        # Default to safe if API fails
        return {
            "is_safe": True,
            "threats": [],
            "warning": f"Could not verify link safety: {str(e)}"
        }


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text"""
    import re
    
    url_pattern = r'https?://\S+|www\.\S+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates


async def check_message_urls(message: str) -> Dict:
    """
    Check all URLs in a message for threats
    
    Returns:
        Dictionary with threat info for each URL
    """
    
    urls = extract_urls_from_text(message)
    threats = {}
    
    for url in urls:
        safety = check_safe_browsing(url)
        threats[url] = safety
    
    return threats
