from pathlib import Path
import pickle
import random
import re
import sys
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import FunctionTransformer

# Add the parent directory to the path so we can import utils
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.preprocess import extract_extra_features

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "DATASET"
MODEL_DIR = BASE_DIR / "model"

EMAIL_PATH = DATA_DIR / "Email" / "emails.csv"
SMS_PATH = DATA_DIR / "sms" / "SMSSpamCollection"
WHATSAPP_PATH = DATA_DIR / "Whatsapp" / "whatsapp_scam_dataset.csv"

RANDOM_STATE = 42
EMAIL_SAMPLE_LIMIT = 20000

HEADER_PATTERN = re.compile(
    r"(?im)^(from|to|cc|bcc|subject|date|message-id|reply-to|mime-version|content-type|content-transfer-encoding|x-[a-z0-9-]+):.*$"
)


def clean_email_body(raw_message: str) -> str:
    if not isinstance(raw_message, str):
        return ""
    text = raw_message.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"\n{2,}", text, maxsplit=1)
    body = parts[1] if len(parts) > 1 else parts[0]
    body = HEADER_PATTERN.sub(" ", body)
    body = re.sub(r"\n", " ", body)
    body = re.sub(r"\s+", " ", body)
    return body.strip()


def sample_email_ham(limit: int = EMAIL_SAMPLE_LIMIT) -> pd.DataFrame:
    messages = []
    for chunk in pd.read_csv(
        EMAIL_PATH,
        usecols=["message"],
        chunksize=50000,
        iterator=True,
        encoding="utf-8",
        low_memory=False,
    ):
        chunk["message"] = chunk["message"].astype(str).map(clean_email_body)
        chunk = chunk[chunk["message"].str.len() > 30]
        messages.extend(chunk["message"].tolist())
        if len(messages) >= limit:
            break

    random.shuffle(messages)
    messages = messages[:limit]
    return pd.DataFrame({"message": messages, "label": "ham", "platform": "email"})


def load_sms_data() -> pd.DataFrame:
    df = pd.read_csv(
        SMS_PATH,
        sep="\t",
        header=None,
        names=["label", "message"],
        encoding="utf-8",
        engine="python",
        quoting=3,  # QUOTE_NONE
    )
    df = df.dropna(subset=["message"])
    df["message"] = df["message"].astype(str)
    df["platform"] = "sms"
    return df


def load_whatsapp_data() -> pd.DataFrame:
    df = pd.read_csv(WHATSAPP_PATH, usecols=["message"], encoding="utf-8")
    df = df.dropna(subset=["message"])
    df["message"] = df["message"].astype(str)
    df["label"] = "spam"
    df["platform"] = "whatsapp"
    return df


def build_pipeline() -> Pipeline:
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.90,
        sublinear_tf=True,
        stop_words="english",
    )
    stats_transformer = FunctionTransformer(extract_extra_features, validate=False)
    feature_union = FeatureUnion(
        [("tfidf", vectorizer), ("stats", stats_transformer)],
        transformer_weights={"tfidf": 1.0, "stats": 0.3},
    )

    pipeline = Pipeline(
        [
            ("features", feature_union),
            ("clf", LogisticRegression(max_iter=3000, class_weight="balanced", C=1.0, random_state=RANDOM_STATE)),
        ]
    )
    return pipeline


def main():
    print("Loading SMS dataset...")
    sms_df = load_sms_data()
    print("Loading WhatsApp dataset...")
    whatsapp_df = load_whatsapp_data()
    print("Sampling email ham data...")
    email_df = sample_email_ham(limit=EMAIL_SAMPLE_LIMIT)

    training_df = pd.concat([sms_df, whatsapp_df, email_df], ignore_index=True)
    training_df = training_df.dropna(subset=["message", "label"])
    training_df = training_df[training_df["label"].isin(["spam", "ham"])].copy()
    training_df = training_df.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

    print("Training dataset composition:")
    print(training_df["platform"].value_counts())
    print(training_df["label"].value_counts())

    X = training_df["message"].astype(str)
    y = training_df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.18,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    pipeline = build_pipeline()
    print("Training the hybrid text classifier...")
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Accuracy: {accuracy:.4f}")
    print(classification_report(y_test, predictions, digits=4))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_DIR / "pipeline.pkl", "wb") as pf:
        pickle.dump(pipeline, pf)

    print("Saved pipeline to", MODEL_DIR / "pipeline.pkl")


if __name__ == '__main__':
    main()
