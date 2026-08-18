# 🪦 Receipt Graveyard

A futuristic privacy-first expense tracker with AI-powered OCR receipt scanning and friend expense splitting. No bank linking. No accounts required.

## ⚡ Tech Stack
- **Backend:** Python + FastAPI + SQLite + SQLAlchemy + Google Gemini AI
- **Frontend:** SvelteKit + Chart.js + Orbitron + Share Tech Mono fonts

## 🚀 Features
- 📷 Scan receipts via Google Gemini AI OCR — extracts merchant, date, items, total, category automatically
- 🪦 Cyberpunk graveyard dashboard — receipts displayed as data pods
- 👻 Split expenses with friends — Equal, Custom, or By Item modes
- 💸 Payment proof system — upload GPay/PhonePe screenshot to confirm settlement
- 📊 Monthly autopsy report — weekly spend chart + top merchants
- 💰 Monthly budget tracker — lock your budget, track consumption, auto-recover when friends pay back
- 🔒 Privacy first — all data stored locally in SQLite, no cloud, no accounts

## 🛠️ Setup & Run

### Prerequisites
- Python 3.13+
- Node.js 18+
- Google Gemini API key (free at aistudio.google.com)

### Backend
```bash
cd backend
pip install -r requirements.txt
echo GEMINI_API_KEY=your_key_here > .env
py -3.13 -m uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## 📁 Project Structure
```
receipt-graveyard/
├── backend/          # FastAPI + SQLite
│   ├── routes/       # receipts, friends, splits, budgets
│   ├── models/       # SQLAlchemy models
│   └── services/     # Gemini OCR service
└── frontend/         # SvelteKit
    └── src/
        ├── routes/   # Dashboard, Scan, Splits, Report
        └── lib/      # API calls, components
```

## 🎨 Design
Synthwave Aurora theme — deep space purple base with neon green, magenta, and aurora purple accents. Orbitron font for headings, Share Tech Mono for data readouts.
