# 🌿 Nayi Disha — Trauma-Informed AI Support Chatbot

A compassionate AI chatbot designed to provide a safe, low-barrier entry point for women and children who have experienced abuse. SafeSpace listens with empathy, validates feelings, and provides real-time trauma categorization to help understand the nature of the situation.

> ⚠️ **Disclaimer:** Nayi Disha is an AI support tool and does **not** replace professional counseling, therapy, or legal advice. If you are in danger, please contact emergency services immediately.

## 🌟 Features

- **Trauma-Informed Responses** — Empathetic, non-judgmental AI trained on real counseling dialogues (MHLCD dataset)
- **Real-Time Trauma Categorization** — Classifies conversations into categories (sexual abuse, domestic violence, cyberbullying, emotional abuse, stalking, child abuse) with confidence scores
- **Crisis Resources** — Always-visible helpline numbers in the sidebar
- **Safety-First Design** — Never asks for personal details, always encourages professional help
- **Session Insights** — Live severity assessment and category tracking

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- A free [Groq API key](https://console.groq.com)

### 1. Clone & Install

```bash
# Using pip
pip install -r requirements.txt
```

### 2. Set Up API Key

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY=gsk_your_key_here
```

### 3. Build the Knowledge Base

This processes the MHLCD counseling dialogue dataset and creates the FAISS vectorstore:

```bash
python ingest_counseling_data.py
```

### 4. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 🌐 Deploy to Streamlit Community Cloud

### 1. Push to GitHub

```bash
git add .
git commit -m "Nayi Disha: trauma-informed AI chatbot"
git push origin main
```

> **Important:** Make sure `vectorstore/db_counseling/` is **not** in `.gitignore` if you want to include the pre-built vectorstore. Otherwise, you'll need to run `ingest_counseling_data.py` on the server.

### 2. Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository, branch (`main`), and set the main file to `app.py`
5. Go to **Advanced settings** → **Secrets** and add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
6. Click **Deploy**

---

## 📁 Project Structure

```
medical-chatbot/
├── app.py                        # Main Streamlit application
├── prompts.py                    # System prompts & templates
├── trauma_classifier.py          # Real-time trauma categorization
├── ingest_counseling_data.py     # Build vectorstore from MHLCD.csv
├── data/
│   ├── MHLCD.csv                 # Counseling dialogue dataset (27,844 rows)
│   └── The_GALE_ENCYCLOPEDIA...  # (Legacy — not used)
├── vectorstore/
│   └── db_counseling/            # FAISS index (built by ingestion script)
├── .streamlit/
│   ├── config.toml               # Streamlit theme configuration
│   └── secrets.toml.example      # Secrets template
├── .env.example                  # Environment variable template
├── .gitignore
├── requirements.txt
├── Pipfile
└── README.md
```

## 🏗️ Architecture

```
User Input → RAG Pipeline (FAISS + Groq LLM) → Empathetic Response
          ↘ Trauma Classifier (Groq LLM) → Session Insights Sidebar
```

- **Knowledge Base:** MHLCD.csv counseling dialogues embedded with `sentence-transformers/all-MiniLM-L6-v2` in FAISS
- **LLM:** Meta Llama 4 Maverick (17B) via Groq API (free tier)
- **UI:** Streamlit with custom dark lavender theme

## 📞 Crisis Resources (India)

| Service | Number |
|---------|--------|
| Emergency | 112 |
| Women Helpline | 181 |
| CHILDLINE | 1098 |
| iCall (Psychosocial) | 9152987821 |
| Vandrevala Foundation | 1860-2662-345 |
| National Commission for Women | 7827-170-170 |

## 🤝 Contributing

This project is built with care for a sensitive audience. If you'd like to contribute, please ensure all changes maintain the trauma-informed, safety-first approach.

## 📄 License

This project is for educational and humanitarian purposes.
