# Umsetzer Video Chunking Pipeline - Technische Dokumentation

## 🎯 Überblick

Die Umsetzer Video Chunking Pipeline ist eine vollständige Lösung zur Verarbeitung von Video-Transkripten für intelligente Q&A-Systeme. Sie transkribiert Videos, teilt sie in semantische Chunks, generiert Embeddings und ermöglicht Retrieval-basierte Antworten.

## 🏗️ Architektur

```
Video Input → Transcription → Semantic Chunking → Embedding Generation → Supabase Storage → Mini Chat Agent
```

### Kernkomponenten:

1. **Transcription Pipeline** (`src/transcription/`)
   - OpenAI Whisper API Integration
   - Audio-Extraktion mit FFmpeg
   - Metadaten-Extraktion (Timestamps)
   - **Content-basierte Video-ID-Generierung** (robust gegen Dateinamen-Änderungen)

2. **Semantic Chunking** (`src/chunking/`)
   - Basierend auf Chroma Research (89.7% Recall)
   - Multiple Strategien: semantic, recursive, video_optimized, fixed
   - Optimale Chunk-Größe: 400 Zeichen mit 50 Zeichen Overlap
   - **Intelligente Timestamp-Zuordnung** (verhindert "0" Timestamps)

3. **Embedding Generation** (`src/embedding/`)
   - OpenAI text-embedding-3-small (1.536 Dimensionen)
   - Batch-Verarbeitung für Effizienz
   - Supabase Integration mit pgvector
   - **Video-Level Duplikat-Erkennung** (verhindert mehrfache Verarbeitung)
   - **Content-basierte Chunk-Duplikat-Erkennung** (robust gegen Chunking-Parameter-Änderungen)

4. **Mini Chat Agent** (`src/agent/`)
   - Retrieval-Augmented Generation (RAG)
   - GPT-4o-mini für Antwort-Generierung
   - Interaktive Chat-Sessions

## 📊 Performance-Metriken

### Chunking-Ergebnisse (1-Stunden-Video):
- **Input**: 303 Segmente, 3.423 Wörter
- **Output**: 57 semantic chunks, 365 Zeichen Durchschnitt
- **Strategie**: Semantic (beste Balance)

### Kosten-Schätzung:
- **Transkription**: ~$0.006 pro Stunde (Whisper API)
- **Embeddings**: $0.0007 pro Video (text-embedding-3-small)
- **Chat**: $0.0015 pro 1K Tokens (GPT-4o-mini)
- **Total für 300 Videos**: ~$0.21

### Kostenersparnis durch Duplikat-Erkennung:
- **Mehrfache Verarbeitung**: Verhindert unnötige Transkriptionen
- **Batch-Runs**: Sicher vor versehentlichen Wiederholungen
- **Entwicklung**: Keine Kosten für Test-Runs
- **Wartung**: Effiziente Updates ohne Duplikate

## 🔧 Aktuelle Verbesserungen

### Intelligente Timestamp-Zuordnung:
- **Problem gelöst**: Keine "0" Timestamps mehr für Chunks, die nicht am Anfang stehen
- **Realistische Chunk-Dauern**: 10-120 Sekunden statt 20+ Minuten
- **Proportionale Zuordnung**: Basierend auf Chunk-Index und Text-Länge
- **Robuste Validierung**: Schutz vor unlogischen Timestamps
- **47x Verbesserung**: Durchschnittsdauer von 22,5 Min auf 0,5 Min reduziert

### Vereinfachte Architektur:
- **Speaker-Detection entfernt**: Whisper unterstützt keine native Speaker-Erkennung
- **Sauberer Code**: Fokus auf die wichtigen Features (Timestamps, Chunking, Embeddings)
- **Bessere Performance**: Weniger Datenverarbeitung ohne Speaker-Logik
- **Wartbarkeit**: Reduzierte Komplexität

## 🔒 Robuste Identifikation

### Video-Level Duplikat-Erkennung:
```python
# 1. Generiere Video-ID (content-basiert)
video_id = self.whisper._generate_video_id(video_file)

# 2. Prüfe ob Video bereits existiert
existing_check = self.processor.supabase_client.client.table("video_chunks").select("video_id").eq("video_id", video_id).limit(1).execute()

# 3. Überspringe Verarbeitung wenn existiert
if existing_check.data:
    logger.info(f"Video {video_id} already exists in database. Skipping processing.")
    return True
```

**Vorteile:**
- ✅ **Verhindert mehrfache Transkription** (kosteneinsparend)
- ✅ **Verhindert mehrfache Verarbeitung** (zeitsparend)
- ✅ **Robust** gegen Whisper API Nicht-Determinismus
- ✅ **Effizient** durch frühe Erkennung

### Content-basierte Video-ID-Generierung:
```python
# Beispiel: video_6938124a12f8_72047833
# - 6938124a12f8: MD5-Hash der ersten 1MB des Videos
# - 72047833: Dateigröße in Bytes
```

**Vorteile:**
- ✅ **Gleiche Video-ID** auch bei verschiedenen Dateinamen
- ✅ **Gleiche Video-ID** auch bei verschiedenen Speicherorten
- ✅ **Robust** gegen Dateinamen-Änderungen und -Verschiebungen

### Content-basierte Chunk-Duplikat-Erkennung:
```python
# Beispiel: 5eb63bbbe01eeed093cb22bb8f5acdc3
# - MD5-Hash des normalisierten Chunk-Texts
# - Normalisiert: Groß-/Kleinschreibung, Leerzeichen
```

**Vorteile:**
- ✅ **Erkennt identische Chunks** auch bei verschiedenen Chunking-Strategien
- ✅ **Erkennt identische Chunks** auch bei verschiedenen Chunk-Indizes
- ✅ **Robust** gegen Chunking-Parameter-Änderungen
- ✅ **Verhindert Duplikate** bei mehrfacher Verarbeitung

### Praktische Auswirkungen:

**Szenario 1: Gleiches Video, mehrfache Verarbeitung**
```bash
# Run 1: video_6938124a12f8_72047833 → 56 Chunks eingefügt
# Run 2: video_6938124a12f8_72047833 → "Video already exists. Skipping processing." ✅
# Result: Keine Duplikate, keine unnötigen Kosten!
```

**Szenario 2: Gleiches Video, anderer Name**
```bash
# Video: "meeting_2025.mp4" → video_6938124a12f8_72047833
# Video: "renamed_meeting.mp4" → video_6938124a12f8_72047833 ✅
# Result: Gleiche Video-ID, Verarbeitung übersprungen!
```

**Szenario 3: Gleiches Video, andere Chunking-Parameter**
```bash
# Chunking mit chunk_size=400 → Chunks 0,1,2,3...
# Chunking mit chunk_size=600 → Chunks 0,1,2...
# Result: Video-Level Check verhindert Verarbeitung komplett!
```

**Szenario 4: Verschiedene Videos**
```bash
# Video A → video_6938124a12f8_72047833
# Video B → video_a1b2c3d4e5f6_12345678
# Result: Verschiedene Video-IDs, beide werden verarbeitet!
```

## 🚀 Setup und Installation

### 1. Umgebungsvorbereitung

```bash
# Virtual Environment erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
```

### 2. FFmpeg Installation (Windows)

```powershell
# Mit winget installieren
winget install "Gyan.FFmpeg" --accept-package-agreements --accept-source-agreements

# PATH aktualisieren
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
```

### 3. Umgebungsvariablen konfigurieren

Kopiere `env_template.txt` zu `.env` und fülle aus:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key_here
SUPABASE_SECRET_KEY=your_supabase_secret_key_here

# Chunking Configuration
CHUNKING_STRATEGY=semantic
CHUNKING_MAX_CHUNK_SIZE=400
CHUNKING_OVERLAP=50
```

## 🚀 Verwendung

### CLI-Tools

Das System bietet mehrere CLI-Tools für verschiedene Anwendungsfälle:

#### CLI-Tools Übersicht

| Tool | Zweck | Verwendung |
|------|-------|------------|
| `process_videos.py` | **Empfohlen** - Benutzerfreundliches CLI | `python process_videos.py --directory videos/` |
| `batch_processor.py` | Kern-Engine für Batch-Verarbeitung | Import in anderen Skripten |
| `tests/test_*.py` | Test-Scripts für einzelne Komponenten | `python tests/test_mini_agent.py` |

**Warum zwei Batch-Tools?**
- `process_videos.py` = Benutzerfreundliches CLI mit Argument-Parsing
- `batch_processor.py` = Kern-Logik, die von anderen Skripten importiert werden kann

#### 1. Batch-Verarbeitung (Empfohlen)
```bash
# Einzelnes Video verarbeiten
python process_videos.py --directory videos/

# Dry-run (nur anzeigen, nicht verarbeiten)
python process_videos.py --directory videos/ --dry-run

# Mit spezifischer Chunking-Strategie
python process_videos.py --directory videos/ --chunking-strategy semantic
```

#### 2. Robuste Pipeline mit Statistiken
```bash
# Batch-Verarbeitung mit detaillierten Statistiken
python batch_processor.py --directory videos/

# Mit verschiedenen Chunking-Strategien
python batch_processor.py --directory videos/ --chunking-strategy recursive
```

#### 3. Tests
```bash
# Alle Komponenten testen
python tests/test_transcription.py
python tests/test_chunking.py
python tests/test_embedding.py
python tests/test_mini_agent.py
```

### CLI-Optionen (process_videos.py)

| Option | Beschreibung | Beispiel |
|--------|--------------|----------|
| `--directory` | Verzeichnis mit Videos verarbeiten | `--directory videos/` |
| `--files` | Spezifische Dateien verarbeiten | `--files video1.mp4 video2.mp4` |
| `--dry-run` | Nur anzeigen, nicht verarbeiten | `--dry-run` |
| `--max-videos` | Max. Anzahl Videos (für Tests) | `--max-videos 10` |
| `--chunking-strategy` | Chunking-Strategie wählen | `--chunking-strategy semantic` |
| `--output` | Ausgabe-Verzeichnis für Transkriptionen | `--output transcriptions/` |

### Verfügbare Chunking-Strategien

| Strategie | Beschreibung | Verwendung |
|-----------|--------------|------------|
| `semantic` | **Empfohlen** - Basierend auf Chroma Research | Beste Balance zwischen Qualität und Performance |
| `recursive` | Hierarchische Text-Aufteilung | Fallback-Option |
| `video_optimized` | Optimiert für Video-Inhalte | Erweiterte Konfiguration |
| `fixed` | Einfache Zeichen-basierte Aufteilung | Einfache Anwendungsfälle |

## 🧪 Testing

### 1. Transkription testen

```bash
python tests/test_transcription.py
```

**Erwartetes Ergebnis:**
- Video wird transkribiert
- JSON-Datei in `transcriptions/` gespeichert
- Metadaten extrahiert (Timestamps, Qualität)

### 2. Chunking testen

```bash
python tests/test_chunking.py
```

**Erwartetes Ergebnis:**
- 4 Strategien verglichen
- Semantic Strategy empfohlen
- Timestamps korrekt zugeordnet

### 3. Embeddings testen

```bash
python tests/test_embedding.py
```

**Erwartetes Ergebnis:**
- 1.536-dimensionale Embeddings generiert
- Mock-Daten in `mock_supabase_data.json` gespeichert
- Kosten-Schätzung angezeigt

### 4. Mini Chat Agent testen

```bash
python tests/test_mini_agent.py
```

**Erwartetes Ergebnis:**
- Agent beantwortet Fragen basierend auf Video-Inhalten
- Confidence-Scores und Quellen angezeigt

### 5. Interaktive Chat-Session

```bash
python tests/test_mini_agent.py --interactive
```

**Verfügbare Befehle:**
- `quit` - Session beenden
- `history` - Gesprächsverlauf anzeigen  
- `clear` - Verlauf löschen
- Normale Fragen - Antworten basierend auf Video-Inhalten

**Beispiel-Session:**
```
❓ Your question: Worum geht es in dem Video?
🤖 Answer: Das Video behandelt das Thema Selbstsabotage und Prokrastination...
📊 Confidence: 1.0
📚 Sources used: 3/5

❓ Your question: Wer spricht in dem Video?
🤖 Answer: Im bereitgestellten Kontext wird nicht explizit erwähnt, wer spricht...
📊 Confidence: 1.0
📚 Sources used: 3/5

❓ Your question: quit
👋 Goodbye!
```

## 📁 Projektstruktur

```
ums__chunking/
├── src/
│   ├── transcription/          # Video-Transkription
│   │   ├── whisper_client.py
│   │   ├── audio_processor.py
│   │   └── metadata_extractor.py
│   ├── chunking/              # Semantic Chunking
│   │   └── semantic_chunker.py
│   ├── embedding/             # Embedding-Generierung
│   │   └── embedding_generator.py
│   ├── agent/                # Mini Chat Agent
│   │   └── mini_chat_agent.py
│   └── utils/                # Hilfsfunktionen
│       └── transcription_utils.py
├── tests/                    # Test-Scripts
├── transcriptions/           # Gespeicherte Transkriptionen
├── config/                   # Konfiguration
├── database/                 # Supabase Schema
└── requirements.txt          # Dependencies
```

## 🔧 Konfiguration

### Chunking-Strategien

| Strategie | Chunk-Größe | Overlap | Verwendung |
|-----------|-------------|---------|------------|
| semantic | 400 | 50 | **Empfohlen** (beste Balance) |
| recursive | 500 | 50 | Fallback-Option |
| video_optimized | 600 | 75 | Erweiterte Konfiguration |
| fixed | 400 | 0 | Einfache Aufteilung |

### Embedding-Konfiguration

- **Model**: text-embedding-3-small
- **Dimensionen**: 1.536
- **Batch-Größe**: 100 (für Effizienz)
- **Kosten**: $0.00002 pro 1K Tokens

## 🗄️ Supabase Setup

### ⚠️ **WICHTIG: Neue Supabase API-Keys**

Supabase hat ihre API-Key-Struktur geändert! Die alten `anon` und `service_role` Keys werden **November 2025** entfernt.

**Neue Keys (empfohlen):**
- **`sb_publishable_...`** - Ersetzt `anon` key (sicher für Frontend)
- **`sb_secret_...`** - Ersetzt `service_role` key (nur für Backend)

**Migration:**
1. Gehe zu [Supabase Dashboard](https://supabase.com/dashboard/project/_/settings/api-keys/new)
2. Generiere neue API-Keys
3. Aktualisiere deine `.env` Datei
4. Teste die Verbindung

**Referenz:** [Supabase API Key Changes](https://github.com/orgs/supabase/discussions/29260)

### 1. Tabelle erstellen

```sql
CREATE TABLE video_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id VARCHAR NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_timestamp FLOAT NOT NULL,
    end_timestamp FLOAT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON video_chunks USING ivfflat (embedding vector_cosine_ops);
```

### 2. pgvector Extension aktivieren

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 🚀 Produktions-Deployment

### 1. Vollständige Pipeline

```python
from src.embedding.embedding_generator import VideoProcessor
from src.chunking.semantic_chunker import SemanticChunker
from src.transcription.whisper_client import WhisperClient

# Video verarbeiten
processor = VideoProcessor()
chunker = SemanticChunker(strategy="semantic")
whisper = WhisperClient()

# Pipeline ausführen
transcription = whisper.transcribe_video("video.mp4")
chunks = chunker.chunk_transcription(transcription.segments, "video_id")
success = processor.process_video_chunks(chunks)
```

### 2. Batch-Verarbeitung für 300 Videos

**Wichtiger Hinweis:** Das System erkennt automatisch bereits verarbeitete Videos und überspringt sie, um Duplikate und unnötige Kosten zu vermeiden.

#### Option A: CLI-Script (empfohlen)

```bash
# Alle Videos in einem Verzeichnis verarbeiten
python process_videos.py --directory videos/

# Spezifische Videos verarbeiten
python process_videos.py --files video1.mp4 video2.mp4

# Mit verschiedenen Chunking-Strategien
python process_videos.py --directory videos/ --chunking-strategy video_optimized

# Nur erste 10 Videos testen
python process_videos.py --directory videos/ --max-videos 10

# Dry-run (zeigen was verarbeitet würde)
python process_videos.py --directory videos/ --dry-run
```

#### Option B: Python-Script

```python
from batch_processor import BatchVideoProcessor
from pathlib import Path

# Batch-Processor initialisieren
processor = BatchVideoProcessor()

# Alle Videos in einem Verzeichnis verarbeiten
video_directory = Path("videos/")
stats = processor.process_video_directory(video_directory)

# Spezifische Videos verarbeiten
video_files = [Path("video1.mp4"), Path("video2.mp4")]
stats = processor.process_video_list(video_files)

print(f"✅ {stats['processed_videos']} videos processed")
print(f"💰 Cost: ${stats['total_cost']:.4f}")
```

## 🔍 Troubleshooting

### Häufige Probleme:

1. **FFmpeg nicht gefunden**
   ```bash
   # Windows: Mit winget installieren
   winget install "Gyan.FFmpeg"
   ```

2. **OpenAI API Key nicht geladen**
   ```bash
   # .env Datei prüfen
   cat .env | grep OPENAI_API_KEY
   ```

3. **Module nicht gefunden**
   ```bash
   # PYTHONPATH setzen
   export PYTHONPATH="."
   ```

4. **Supabase-Verbindung fehlschlägt**
   - Credentials in `.env` prüfen
   - Tabelle in Supabase erstellt?
   - pgvector Extension aktiviert?

## 📈 Erweiterungsmöglichkeiten

### 1. Erweiterte Chunking-Strategien
- Topic-basierte Segmentierung
- Dynamische Chunk-Größen
- Kontext-bewusste Chunking

### 2. Multi-Modal Features
- Video-Thumbnails zu Chunks
- Audio-Features extrahieren
- OCR für Slides/Text

### 3. Advanced RAG
- Hybride Suche (Vector + Keyword)
- Re-Ranking mit Cross-Encoder
- Context-Compression

### 4. Monitoring & Analytics
- Chunk-Qualitäts-Metriken
- User-Interaktion-Tracking
- Performance-Monitoring

## 📚 Referenzen

- [Chroma Research: Evaluating Chunking](https://research.trychroma.com/evaluating-chunking)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [Supabase pgvector](https://supabase.com/docs/guides/database/extensions/pgvector)
- [LangChain RAG](https://python.langchain.com/docs/use_cases/question_answering/)

## 🤝 Support

Bei Fragen oder Problemen:
1. Checke die Test-Scripts für Beispiele
2. Prüfe die Logs für Fehlermeldungen
3. Stelle sicher, dass alle Dependencies installiert sind
4. Verifiziere die API-Keys und Supabase-Credentials

---

**Version**: 1.2.0  
**Letzte Aktualisierung**: September 2025  
**Kompatibilität**: Python 3.8+, Windows/Linux/Mac
