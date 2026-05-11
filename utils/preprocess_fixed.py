import re


def normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ''

    text = text.lower().strip()
    text = re.sub(r'https?://\S+|www\.\S+|\.com|\.in|\.org', ' urltoken ', text)
    text = re.sub(r'\S+@\S+', ' emailtoken ', text)
    text = re.sub(r'\d{3,}', ' numbertoken ', text)
    text = re.sub(r'\r\n|\r|\n', ' ', text)
    text = re.sub(
        r'(?im)^(from|to|cc|bcc|subject|date|message-id|reply-to|mime-version|content-type|content-transfer-encoding|x-[a-z0-9-]+):.*$",
        ' ',
        text,
        flags=re.M,
    )
    text = re.sub(r'[^a-z0-9\s!?$%]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
