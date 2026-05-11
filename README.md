# UniSpam AI

Universal Multi-Platform Spam Detection using Hybrid Intelligence (Machine Learning + Rule-Based Analysis).

## Features

- Detects spam across Email, SMS, WhatsApp, and Other platforms
- Hybrid approach: TF-IDF + Logistic Regression + Rule Engine
- Provides confidence scores, reasons, and platform-specific insights
- Web interface with real-time analysis

## Requirements

- Python 3.8+
- Dependencies: See `requirements.txt`

## Installation

1. Clone or download the project.
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Training the Model

The model is pre-trained, but to retrain:

```
python model/train_model.py
```

This uses the SMS Spam Collection dataset (5,572 samples) for high accuracy (~98.65%).

## Running the Application

1. Activate the virtual environment (if not already):
   ```
   venv\Scripts\activate  # Windows
   ```
2. Start the server:
   ```
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
3. Open your browser and go to: `http://localhost:8000`

## API Endpoints

- `GET /`: Web interface
- `POST /predict`: Predict spam
  - Body: `platform` (email/sms/whatsapp/other), `message` (text)
- `GET /health`: Health check

## Example API Usage

```bash
curl -X POST "http://localhost:8000/predict" \
     -d "platform=sms&message=URGENT! Your account is locked."
```

## Technologies

- FastAPI (Backend)
- Scikit-learn (ML)
- Jinja2 (Templates)
- Uvicorn (Server)