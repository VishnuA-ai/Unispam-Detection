# 🚀 UniSpam AI v2.0 - Production Setup Guide

## ✨ What's New in v2.0

- 🌐 **Bilingual Support**: Full English + Tamil UI
- 📱 **Mobile-First Design**: Tailwind CSS responsive layout  
- 🎯 **Language Persistence**: localStorage + URL parameters
- 🖼️ **OCR Integration**: Screenshot text extraction via OCR.Space API (FREE)
- 🤖 **AI Reasoning**: Gemini 1.5 Flash for bilingual spam reasons (FREE tier)
- 🛡️ **Safe Browsing**: Google Safe Browsing API integration (optional)
- ⚡ **Fully Async**: FastAPI with async/await throughout
- 🎨 **Tailwind CSS**: Modern, responsive, eye-friendly UI

## 📋 System Requirements

- Python 3.10+
- Virtual environment (venv)
- 2GB RAM minimum
- Internet connection (for API calls)

## 🔧 Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd "d:\UNISPAM PROJECT"

# Activate virtual environment
venv\Scripts\activate

# Install/upgrade packages
pip install -r requirements.txt
```

### Step 2: Get Free API Keys

#### 🤖 Gemini 1.5 Flash (Required for AI Reasons)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Click "Create API Key"
3. Copy the key

#### 🔗 Google Safe Browsing (Optional - URL verification)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable "Safe Browsing API"
4. Create API key
5. Copy the key

#### 📸 OCR.Space (Already included - FREE tier)
- No setup needed! Demo API key is pre-configured
- Free tier: 25 requests/day
- For higher limits, get key from [OCR.Space](https://ocr.space/ocrapi)

### Step 3: Configure Environment Variables

Copy the example file and add your keys:

```bash
# Windows PowerShell:
cp .env.example .env

# Edit .env with your API keys
# For Notepad:
notepad .env
```

**Required:**
```
GEMINI_API_KEY=your_key_from_google_ai_studio
```

**Optional:**
```
GOOGLE_SAFE_BROWSING_API_KEY=your_safe_browsing_key
```

### Step 4: Train/Load Model

The ML model is already pre-trained and saved in `model/pipeline.pkl` (99.28% accuracy).

To retrain with new data:
```bash
python model/train_model.py
```

### Step 5: Start the App

```bash
# Development mode (with auto-reload):
python app.py

# Or use uvicorn directly:
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Access the App

Open your browser:
- **Main Page**: http://localhost:8000
- **Language Selection**: http://localhost:8000/ (redirects automatically)
- **Health Check**: http://localhost:8000/health

## 📱 Feature Overview

### 1. Language Selection
- First visit: Choose English or Tamil
- Selection saved to localStorage
- Can toggle anytime with 🌐 button

### 2. Platform Selection
- 📧 Email
- 📱 SMS
- 💚 WhatsApp
- 📱 Other

### 3. Spam Detection
- ML Model (scikit-learn): 99.28% accuracy
- Rule-Based Engine: Link verification, urgency detection, reward/prize detection
- Safe Browsing: URL threat checking (optional)
- AI Reasoning: Gemini-powered bilingual reasons

### 4. Screenshot Scanning
- Click "Scan Screenshot" button
- Select image (PNG, JPG, JPEG)
- OCR extracts text automatically
- Analyzes extracted text as spam

### 5. Results Display
- **Risk Level**: Color-coded (Red/Orange/Green)
- **Confidence Meter**: 0-100% visual bar
- **Verdict**: Spam or Not Spam
- **ML Probability**: Model's confidence
- **Rule Score**: Rule-engine score
- **Reasons**: AI-generated bilingual explanations
- **Platform Insight**: Platform-specific tips
- **Highlighted Text**: Suspicious terms highlighted

## 🌍 Bilingual Support

Both English and Tamil UI elements:
- ✅ All buttons and labels
- ✅ Placeholder text
- ✅ Error messages
- ✅ Platform insights
- ✅ Sample messages (load via "Load Sample" button)
- ✅ AI-generated spam reasons (when Gemini configured)

Switch languages anytime: Click 🌐 EN/TA button in top-right

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'fastapi'"
**Solution:**
```bash
pip install -r requirements.txt
```

### Problem: "GEMINI_API_KEY not found"
**Solution:**
1. Get key from [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Add to `.env` file
3. Restart app

### Problem: "Connection refused" on http://localhost:8000
**Solution:**
- Check if app is running: Look for "Uvicorn running on..."
- Try different port: `uvicorn app:app --port 8001`

### Problem: "OCR failed" or "Failed to process screenshot"
**Solution:**
- Check file size (max 5MB recommended)
- Try different image format (PNG/JPG)
- Free tier may have rate limit - wait a minute and retry

### Problem: OCR returns garbled Tamil text
**Solution:**
- OCR.Space works best for English text
- For Tamil: Gemini's AI reasoning will still provide good results
- Consider using clear, high-contrast screenshots

## 📊 API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Language selection page |
| `/index.html` | GET | Main app page |
| `/translations` | GET | Bilingual JSON data |
| `/predict` | POST | Spam detection (form: platform, message, language) |
| `/ocr-scan` | POST | Screenshot OCR (file: image, form: language) |
| `/health` | GET | Health check |

## 🚀 Production Deployment

### Option 1: Local Network Access
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```
Access from any machine: `http://your_ip:8000`

### Option 2: Azure App Service (Recommended)
```bash
# Install Azure CLI
# Then deploy using azd or manual upload
```

### Option 3: Docker (Optional)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🎯 Free API Limits

| Service | Tier | Limit | Cost |
|---------|------|-------|------|
| **Gemini 1.5 Flash** | Free | 15 requests/minute | FREE |
| **OCR.Space** | Free | 25 requests/day | FREE |
| **Safe Browsing** | Free (if using Cloud Free) | 10,000/day | FREE* |

*Safe Browsing: Google Cloud free tier expires after 12 months; then pay per API call

## 📁 Project Structure

```
d:\UNISPAM PROJECT\
├── app.py                    # FastAPI app (v2.0 - async, bilingual)
├── requirements.txt          # Dependencies (with new API libs)
├── .env.example             # Environment template (API keys)
├── translations.json        # Bilingual UI text
│
├── templates/
│   ├── index.html           # Main app (Tailwind redesign)
│   └── language-select.html # Language landing page
│
├── static/
│   └── style.css            # CSS (minimal - mostly Tailwind)
│
├── utils/
│   ├── preprocess.py        # Text processing
│   ├── rules.py             # Rule-based spam detection
│   ├── ai_services.py       # Gemini AI integration
│   └── security.py          # OCR + Safe Browsing
│
├── model/
│   ├── train_model.py       # Model training script
│   └── pipeline.pkl         # Trained ML model (99.28% accuracy)
│
└── DATASET/                 # Training data (Email, SMS, WhatsApp)
```

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] App starts without errors
- [ ] Can access http://localhost:8000
- [ ] Language selection works (EN/TA toggle)
- [ ] Can analyze sample messages
- [ ] Results display with color coding
- [ ] Confidence meter shows correctly
- [ ] Try "Load Sample" button in both languages
- [ ] Screenshot scanning loads file picker
- [ ] ML probability shown correctly
- [ ] Platform selection works (4 buttons)
- [ ] Mobile view responsive on phone/tablet

## 🎓 Testing Guide

### Test 1: Spam Detection (English)
1. Select "Email" platform
2. Enter: "URGENT! Confirm your bank account NOW or it will be SUSPENDED"
3. Expected: High spam confidence, red risk level

### Test 2: Not Spam (English)
1. Select "SMS" platform
2. Enter: "Hey, are you free for lunch tomorrow at 1 PM?"
3. Expected: Low spam confidence, green risk level

### Test 3: Bilingual (Tamil)
1. Click 🌐 EN/TA to switch to Tamil
2. All UI text should be in Tamil
3. Try Tamil message: "உடனடிவெற்றி பெறவும்!" (win instantly)
4. Expected: AI reasons in Tamil (if Gemini configured)

### Test 4: OCR Scanning
1. Take screenshot of a phishing email
2. Click "Scan Screenshot"
3. Select image file
4. Text should extract and auto-analyze

## 📞 Support

**Issues or questions?**
- Check `.env` configuration
- Review error logs in terminal
- Verify API keys are correct
- Check API rate limits

## 🎉 You're Done!

Your production UniSpam AI app is ready!

**Key Features:**
- ✅ Mobile-first responsive design
- ✅ Bilingual (English + Tamil)
- ✅ Free API integrations
- ✅ 99.28% ML accuracy
- ✅ Screenshot OCR scanning
- ✅ Real-time URL safety checking
- ✅ AI-powered bilingual reasoning
- ✅ Full async backend

Start detecting spam like a pro! 🚀
