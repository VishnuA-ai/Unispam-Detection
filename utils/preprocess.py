import re
import numpy as np


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ''

    text = text.lower().strip()
    text = re.sub(r'https?://\S+|www\.\S+|\.com|\.in|\.org', ' urltoken ', text)
    text = re.sub(r'\S+@\S+', ' emailtoken ', text)
    text = re.sub(r'\d{3,}', ' numbertoken ', text)
    text = re.sub(r'\r\n|\r|\n', ' ', text)
    text = re.sub(
        r'(?im)^(from|to|cc|bcc|subject|date|message-id|reply-to|mime-version|content-type|content-transfer-encoding|x-[a-z0-9-]+):.*$',
        ' ',
        text,
        flags=re.M,
    )
    text = re.sub(r'[^a-z0-9\s!?$%]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


URL_PATTERN = re.compile(r"https?://\S+|www\.|\.com|\.in|\.org", re.IGNORECASE)
KEYWORD_PATTERN = re.compile(
    r"\b(urgent|act now|limited time|free|win|lottery|claim|click|verify|otp|offer|congratulations|cash|prize|bank|refund|loan|account|upi|payment|password|login|verify now)\b",
    re.IGNORECASE,
)


def extract_extra_features(messages):
    rows = []
    for text in np.asarray(messages, dtype=str):
        rows.append([
            len(text),
            len(re.findall(r"\d", text)),
            len(URL_PATTERN.findall(text)),
            len(re.findall(r"[!?$%]", text)),
            len(re.findall(r"[A-Z]", text)),
            len(re.findall(r"[A-Z]{2,}", text)),
            len(KEYWORD_PATTERN.findall(text)),
        ])
    return np.asarray(rows, dtype=float)
