# UMS_BastiAI

Ein intelligenter Video Chat Agent mit Bastians charakteristischem Performance-Coach Ton.

## 🚀 Features

- **Basti O-Ton**: Automatisch aktivierter charakteristischer Performance-Coach Stil
- **Video Content Q&A**: Intelligente Beantwortung von Fragen zu Video-Inhalten
- **Confidence Scoring**: Vertrauens-Score für jede Antwort
- **Debug Mode**: Detaillierte Informationen über Quellen und Verarbeitung
- **Responsive Design**: Funktioniert auf allen Geräten

## 🛠️ Installation

### Lokale Entwicklung

```bash
# Repository klonen
git clone https://github.com/your-username/UMS_BastiAI.git
cd UMS_BastiAI

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements_streamlit.txt

# Environment Variables setzen
cp env_streamlit_template.txt .env
# .env Datei mit Ihren API Keys bearbeiten

# App starten
streamlit run streamlit_app.py
```

### Streamlit Cloud Deployment

1. Repository zu GitHub pushen
2. Auf [share.streamlit.io](https://share.streamlit.io) gehen
3. "New app" auswählen
4. Repository und `streamlit_app.py` als Main File auswählen
5. Environment Variables setzen:
   - `OPENAI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `SUPABASE_SECRET_KEY`

## 🔧 Konfiguration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
SUPABASE_SECRET_KEY=your_supabase_secret_key

# Agent Configuration
AGENT_LLM_MODEL=gpt-4o-mini
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=1000
AGENT_TOP_K=5
AGENT_SIMILARITY_THRESHOLD=0.7
```

## 🎯 Basti O-Ton

Der Basti O-Ton ist standardmäßig aktiviert und verwendet einen charakteristischen Performance-Coach Stil:

- **Direkte "du" Ansprache**
- **Kurze, prägnante Sätze**
- **Motivierende Sprache**
- **Business-Jargon und Psycho-Vokabular**
- **Emotionale Trigger und Handlungsaufforderungen**

## 📊 Kosten

- **Streamlit Cloud**: KOSTENLOS
- **OpenAI API**: ~$0.0001-0.0002 pro Frage
- **Supabase**: KOSTENLOS (Free Tier)

## 🛠️ Entwicklung

### Projektstruktur

```
UMS_BastiAI/
├── streamlit_app.py          # Hauptanwendung
├── requirements_streamlit.txt # Dependencies
├── src/
│   ├── agent/               # Chat Agent
│   ├── embedding/           # Embedding Generator
│   ├── transcription/       # Audio Processing
│   └── utils/              # Utilities
├── config/                  # Konfiguration
└── tests/                   # Tests
```

### Tests ausführen

```bash
python -m pytest tests/
```

## 📝 Lizenz

Dieses Projekt ist für interne Verwendung bestimmt.

## 🤝 Support

Bei Fragen oder Problemen, bitte ein Issue erstellen oder den Debug-Modus in der App aktivieren.