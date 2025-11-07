"""
Streamlit Web Interface for Video Chat Agent
"""

import streamlit as st
import logging
from pathlib import Path
import sys
from datetime import datetime
import time
import os

# Setup imports for cloud deployment
try:
    from import_helper import setup_imports, get_agent, get_settings
    setup_imports()
    MiniChatAgent = get_agent()
    settings = get_settings()
    logger = logging.getLogger(__name__)
    logger.info("✅ Imports erfolgreich geladen")
except ImportError as e:
    # Fallback to direct imports
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        from src.agent.mini_chat_agent import MiniChatAgent
        from config.settings import settings
        logger = logging.getLogger(__name__)
        logger.info("✅ Imports erfolgreich geladen (fallback)")
    except ImportError as e2:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Import-Fehler: {e2}")
        st.error(f"Import-Fehler: {e2}")
        st.stop()
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Unerwarteter Fehler beim Import: {e}")
    st.error(f"Unerwarteter Fehler: {e}")
    st.stop()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Page configuration
st.set_page_config(
    page_title="BastiAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Apple-inspired monochrome styling
st.markdown("""
<style>
:root {
    color-scheme: dark;
    --border-color: rgba(255, 255, 255, 0.25);
}
html, body, [class*="stApp"] {
    background-color: #000;
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, system-ui, sans-serif;
}
div[data-testid="stDecoration"] {
    display: none !important;
}
section[data-testid="stSidebar"] {
    display: none !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
a {
    color: #fff;
}
.stMarkdown, .stMarkdown p, label, span, p, h1, h2, h3, h4, h5, h6, div {
    color: inherit;
}
.stButton > button {
    background-color: #fff;
    color: #000;
    border-radius: 18px;
    border: 2px solid #fff;
    padding: 0.6rem 1.6rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background-color: #000;
    color: #fff;
    border-color: #fff;
}
.stButton > button:focus:not(:active) {
    outline: 2px solid #fff;
}
.stTextArea textarea,
.stTextInput input,
[data-baseweb="input"] input {
    background: rgba(255, 255, 255, 0.05);
    color: #fff;
    border: 2px solid rgba(255, 255, 255, 0.25);
    border-radius: 18px;
}
.stTextArea textarea:focus,
.stTextInput input:focus,
[data-baseweb="input"] input:focus {
    border-color: #fff;
    box-shadow: none !important;
}
.stSelectbox div[data-baseweb="select"] {
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.25);
    border-radius: 18px;
}
.stSelectbox div[data-baseweb="select"]:hover {
    border-color: #fff;
}
.stSlider > div span[data-baseweb="slider-handle"] {
    background-color: #fff;
}
.stSlider > div div[data-baseweb="slider"] {
    background-color: rgba(255, 255, 255, 0.3);
}
.stSlider > div div[data-testid="stTickBar"] {
    background: transparent;
}
.stAlert {
    background: rgba(255, 255, 255, 0.04);
    border: 2px solid var(--border-color);
    border-radius: 18px;
    color: #fff !important;
}
.stAlert * {
    color: #fff !important;
}
.stMetric {
    background: rgba(255, 255, 255, 0.04);
    border: 2px solid var(--border-color);
    border-radius: 18px;
    padding: 1rem 1.4rem;
}
[data-testid="stMetricValue"],
[data-testid="stMetricLabel"],
[data-testid="stMetricDelta"] {
    color: #fff !important;
}
hr {
    border-color: rgba(255, 255, 255, 0.15) !important;
}
.menu-panel {
    border: 2px solid var(--border-color);
    border-radius: 24px;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.02);
    margin-bottom: 2rem;
}
.status-strip {
    border: 2px solid var(--border-color);
    border-radius: 18px;
    padding: 0.75rem 1.2rem;
    background: rgba(255, 255, 255, 0.02);
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
    letter-spacing: 0.04em;
}
.logo-container {
    display: inline-flex;
    align-items: center;
    justify-content: flex-start;
    padding: 0.75rem 1.2rem;
    border: 2px solid var(--border-color);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.02);
}
.logo-container svg {
    width: 140px;
    height: auto;
    opacity: 0.85;
}
.app-title {
    font-size: 2.2rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    margin-bottom: 0.4rem;
}
.app-subtitle {
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 0.4em;
    color: rgba(255, 255, 255, 0.55);
}
.chat-message {
    padding: 1.1rem;
    border-radius: 20px;
    margin: 1rem 0;
    border: 2px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.03);
}
.user-message {
    background: rgba(255, 255, 255, 0.08);
}
.bot-message {
    background: rgba(255, 255, 255, 0.02);
}
.confidence-badge {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    border: 2px solid rgba(255, 255, 255, 0.3);
    margin-top: 0.6rem;
    text-transform: uppercase;
}
.confidence-high {
    border-color: #fff;
    color: #000;
    background: #fff;
}
.confidence-medium {
    border-color: rgba(255, 255, 255, 0.6);
    color: #fff;
}
.confidence-low {
    border-color: rgba(255, 255, 255, 0.3);
    color: #fff;
}
.chat-input-card {
    border: 2px solid var(--border-color);
    border-radius: 24px;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.03);
    margin-top: 1.8rem;
}
.note {
    border: 2px solid var(--border-color);
    border-radius: 18px;
    padding: 1rem 1.3rem;
    background: rgba(255, 255, 255, 0.02);
    font-size: 0.85rem;
    letter-spacing: 0.02em;
}
</style>
""", unsafe_allow_html=True)

def get_confidence_class(confidence):
    """Get CSS class for confidence badge"""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, (int, float)):
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        return f"{minutes:02d}:{seconds:02d}"
    return str(timestamp)

def initialize_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    if 'debug_mode_ai' not in st.session_state:
        st.session_state.debug_mode_ai = False
    if 'basti_tone' not in st.session_state:
        st.session_state.basti_tone = True  # Default: Basti O-Ton aktiviert
    if 'basti_tone_v2' not in st.session_state:
        st.session_state.basti_tone_v2 = False  # Default: O-Ton-BASTI-AI2 deaktiviert
    if 'mock_data_active' not in st.session_state:
        st.session_state.mock_data_active = False
    if 'clarification_mode' not in st.session_state:
        st.session_state.clarification_mode = False
    if 'iterative_clarification_mode' not in st.session_state:
        st.session_state.iterative_clarification_mode = False  # Default: deaktiviert
    if 'creativity_level' not in st.session_state:
        st.session_state.creativity_level = 0.0  # Default: Maximal quelltreu
    if 'selected_chunk_table' not in st.session_state:
        st.session_state.selected_chunk_table = 'video_chunks_video_optimized'  # Default table
    if 'menu_open' not in st.session_state:
        st.session_state.menu_open = False
    if 'test_mode' not in st.session_state:
        st.session_state.test_mode = False
    if 'chunk_table_error' not in st.session_state:
        st.session_state.chunk_table_error = None

def load_logo_svg() -> str:
    """Return Umsetzer logo SVG as string."""
    logo_path = Path(__file__).parent / "assets" / "umsetzer_logo.svg"
    if logo_path.exists():
        return logo_path.read_text(encoding="utf-8")
    return ""

def apply_selected_chunk_table():
    """Ensure agent uses the selected chunk table."""
    selected_table = st.session_state.get('selected_chunk_table', 'video_chunks_video_optimized')
    if st.session_state.agent:
        try:
            st.session_state.agent.set_chunk_table(selected_table)
        except Exception as exc:
            st.session_state.chunk_table_error = str(exc)
        else:
            st.session_state.chunk_table_error = None

def note_block(text: str):
    """Render a neutral monochrome note block."""
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)

def rerun_app():
    """Rerun Streamlit app compatibly across versions."""
    try:
        if hasattr(st, "experimental_rerun"):
            rerun_app()
        elif hasattr(st, "rerun"):
            rerun_app()
    except AttributeError:
        if hasattr(st, "rerun"):
            rerun_app()

def render_control_panel():
    """Render collapsible control panel with all settings and debug tools."""
    st.markdown('<div class="menu-panel">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Menü & Debug")

    query_params = st.query_params
    if 'debug' in query_params:
        debug_param = query_params['debug']
        if isinstance(debug_param, list):
            debug_param = debug_param[0]
        url_debug = str(debug_param).lower() in ["true", "1", "yes", "on"]
        if url_debug != st.session_state.debug_mode:
            st.session_state.debug_mode = url_debug
            rerun_app()

    st.markdown("#### Systemsteuerung")
    st.session_state.debug_mode = st.checkbox(
        "Debug-Modus aktivieren",
        value=st.session_state.debug_mode,
        help="Zeigt zusätzliche Informationen wie Quellen und Verarbeitungszeiten an."
    )
    st.session_state.debug_mode_ai = st.checkbox(
        "🤖 Debug-Modus mit AI-Funktionen",
        value=st.session_state.debug_mode_ai,
        help="⚠️ Sehr rechenintensiv – aktiviert detaillierte Qualitätsanalysen (Chunk Coverage, Knowledge Gap, Hallucination Risk)."
    )

    st.markdown("#### Kreativitätsstufe")
    creativity_level = st.slider(
        "Quelltreue vs. Kreativität",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.creativity_level,
        step=0.1,
        help="Steuert, wie strikt Antworten an den Video-Chunks bleiben sollen."
    )
    st.session_state.creativity_level = creativity_level
    if creativity_level <= 0.3:
        note_block(f"🔒 Sehr restriktiv ({creativity_level:.1f}) – nur Informationen aus den Chunks.")
    elif creativity_level <= 0.6:
        note_block(f"⚖️ Ausgewogen ({creativity_level:.1f}) – Chunks mit leichten Ergänzungen.")
    else:
        note_block(f"🎨 Kreativ ({creativity_level:.1f}) – Chunks mit erweiterten Ergänzungen.")

    st.markdown("#### O-Ton Optionen")
    st.session_state.basti_tone = st.checkbox(
        "Basti O-Ton aktivieren",
        value=st.session_state.basti_tone,
        help="Aktiviert den statischen Performance-Coach Ton."
    )
    st.session_state.basti_tone_v2 = st.checkbox(
        "🎭 O-Ton-BASTI-AI2-Modus",
        value=st.session_state.basti_tone_v2,
        help="Dynamischer Stil: analysiert den Sprachstil aus den Chunks."
    )
    if st.session_state.basti_tone and st.session_state.basti_tone_v2:
        note_block("⚠️ Beide O-Ton-Modi aktiv – O-Ton-BASTI-AI2 hat Priorität.")

    st.markdown("#### Nachfrage-Modus")
    st.session_state.clarification_mode = st.checkbox(
        "🤔 Nachfrage-Modus aktivieren",
        value=st.session_state.clarification_mode,
        help="Aktiviert automatische Nachfragen bei unspezifischen Fragen."
    )
    st.session_state.iterative_clarification_mode = st.checkbox(
        "🔄 Iterativer Nachfrage-Modus",
        value=st.session_state.iterative_clarification_mode,
        help="Sammelt Informationen Schritt für Schritt, bevor eine finale Antwort erstellt wird."
    )

    if st.session_state.agent:
        st.session_state.agent.toggle_clarification_mode(st.session_state.clarification_mode)
        st.session_state.agent.toggle_iterative_clarification_mode(st.session_state.iterative_clarification_mode)

    st.markdown("#### Datenbasis")
    available_tables = [
        "video_chunks",
        "video_chunks_recursive",
        "video_chunks_video_optimized",
        "video_chunks_fixed",
    ]
    current_table = st.session_state.get('selected_chunk_table', 'video_chunks_video_optimized')
    selected_table = st.selectbox(
        "Tabelle auswählen",
        options=available_tables,
        index=available_tables.index(current_table) if current_table in available_tables else 0,
        help="Wählt die Supabase-Tabelle für die Chunk-Suche."
    )
    st.session_state.selected_chunk_table = selected_table
    apply_selected_chunk_table()

    table_labels = {
        "video_chunks": "Semantic (Standard)",
        "video_chunks_recursive": "Recursive",
        "video_chunks_video_optimized": "Video Optimized",
        "video_chunks_fixed": "Fixed",
    }
    table_label = table_labels.get(selected_table, selected_table)
    if st.session_state.chunk_table_error:
        note_block(f"⚠️ Konnte Tabelle nicht setzen: {st.session_state.chunk_table_error}")
    else:
        note_block(f"✅ Aktive Datenbasis: {table_label} ({selected_table})")

    st.markdown("#### Diagnose")
    st.session_state.test_mode = st.checkbox(
        "🔧 Test-Modus aktivieren",
        value=st.session_state.test_mode,
        help="Führt schnelle Verbindungstests zu OpenAI und Supabase aus."
    )

    if st.session_state.test_mode:
        st.markdown("##### Verbindungstest")
        with st.spinner("Teste Verbindungen..."):
            test_results = test_connections()

        col1, col2 = st.columns(2)
        with col1:
            note_block("✅ OpenAI") if test_results['openai'] else note_block("⚠️ OpenAI fehlgeschlagen")
            note_block("✅ Supabase") if test_results['supabase'] else note_block("⚠️ Supabase fehlgeschlagen")
        with col2:
            note_block("✅ Datenbank erreichbar") if test_results['database_query'] else note_block("⚠️ Datenbank nicht erreichbar")
            note_block(f"📊 Gefundene Chunks: {test_results['chunks_found']}")

        if test_results['error_messages']:
            for error in test_results['error_messages']:
                note_block(f"⚠️ {error}")

    st.markdown("#### Supabase Debug")
    if st.button("Supabase-Verbindung testen", key="supabase_debug_button"):
        with st.spinner("Teste Supabase-Verbindung..."):
            try:
                if st.session_state.agent:
                    supabase_client = st.session_state.agent.video_processor.supabase_client

                    if supabase_client.mock_mode:
                        note_block("⚠️ Supabase im Mock-Modus – keine echte Verbindung.")
                        st.markdown("**Grund:** Supabase-Credentials nicht gefunden.")
                        st.markdown("**Lösung:** Credentials in Streamlit Cloud Secrets oder Environment Variablen hinterlegen.")

                        st.markdown("##### Debug: Verfügbare Credentials")
                        try:
                            from config.settings import settings

                            st.markdown("**Via Settings:**")
                            note_block(f"SUPABASE_URL: {'✅ gesetzt' if settings.supabase_url else '⚠️ fehlt'}")
                            note_block(f"SUPABASE_PUBLISHABLE_KEY: {'✅ gesetzt' if settings.supabase_publishable_key else '⚠️ fehlt'}")
                            note_block(f"SUPABASE_SECRET_KEY: {'✅ gesetzt' if settings.supabase_secret_key else '⚠️ fehlt'}")
                            note_block(f"OPENAI_API_KEY: {'✅ gesetzt' if settings.openai_api_key else '⚠️ fehlt'}")

                        except Exception as settings_error:
                            note_block(f"⚠️ Fehler beim Laden der Settings: {settings_error}")

                        st.markdown("##### Mock-Daten für Tests")
                        if st.button("Mock-Daten aktivieren", key="activate_mock_data"):
                            st.session_state.mock_data_active = True
                            note_block("✅ Mock-Daten aktiviert – Sie können jetzt Fragen stellen.")

                    else:
                        note_block("✅ Supabase-Verbindung aktiv.")
                        test_query = "Performance"
                        st.markdown(f"**Test-Suche:** '{test_query}'")
                        results = supabase_client.search_similar_chunks([0.1] * 1536, limit=5)
                        note_block(f"📊 Gefundene Chunks: {len(results)}")
                        if results:
                            note_block("✅ Chunks gefunden – hier die ersten Einträge:")
                            for idx, chunk in enumerate(results[:3], 1):
                                st.markdown(f"{idx}. {chunk.get('chunk_text', '')[:120]}…")
                        else:
                            note_block("⚠️ Keine Chunks gefunden – bitte Datenbank prüfen.")
                else:
                    note_block("⚠️ Agent nicht initialisiert.")
            except Exception as supabase_error:
                note_block(f"⚠️ Fehler beim Supabase-Test: {supabase_error}")

    st.markdown("#### Aktionen")
    if st.button("🗑️ Chat-Verlauf löschen", key="clear_history_button"):
        st.session_state.chat_history = []
        if st.session_state.agent:
            st.session_state.agent.clear_history()
        rerun_app()

    if st.button("🔄 Voll automatischer iterativer Test", key="auto_test_button"):
        if st.session_state.agent:
            with st.spinner("Führe automatischen iterativen Test durch..."):
                result = run_automatic_iterative_test()
                if result:
                    st.session_state.test_result = result
                    note_block("✅ Automatischer Test abgeschlossen – Ergebnisse erscheinen im Hauptfenster.")
                    rerun_app()
        else:
            note_block("⚠️ Agent nicht initialisiert.")

    if hasattr(st.session_state, 'test_result') and st.session_state.test_result:
        note_block("📊 Test-Ergebnisse werden im Hauptfenster angezeigt.")

    if st.session_state.get('mock_data_active'):
        note_block("🧪 Mock-Daten aktiv – für Live-Betrieb Supabase-Verbindung herstellen.")

    st.markdown('</div>', unsafe_allow_html=True)

def initialize_agent():
    """Initialize the chat agent"""
    if st.session_state.agent is None:
        try:
            with st.spinner("Initialisiere Chat Agent..."):
                st.session_state.agent = MiniChatAgent()
                
                # Set initial chunk table if selected
                selected_table = st.session_state.get('selected_chunk_table', 'video_chunks_video_optimized')
                try:
                    st.session_state.agent.set_chunk_table(selected_table)
                    logger.info(f"Agent initialized with table: {selected_table}")
                except Exception as e:
                    logger.warning(f"Could not set initial table: {e}")
                
                # Check if Supabase is in mock mode and auto-activate mock data
                if hasattr(st.session_state.agent, 'video_processor'):
                    supabase_client = st.session_state.agent.video_processor.supabase_client
                    if supabase_client.mock_mode:
                        st.session_state.mock_data_active = True
                        logger.info("Supabase in mock mode - auto-activating mock data")
                        st.info("🧪 Mock-Daten automatisch aktiviert (Supabase nicht verfügbar)")
                
            st.success("Chat Agent erfolgreich initialisiert!")
            return True
        except Exception as e:
            st.error(f"Fehler beim Initialisieren des Chat Agents: {e}")
            logger.error(f"Agent initialization failed: {e}")
            return False
    else:
        # Agent already exists, update table if changed
        selected_table = st.session_state.get('selected_chunk_table', 'video_chunks_video_optimized')
        try:
            st.session_state.agent.set_chunk_table(selected_table)
        except Exception as e:
            logger.warning(f"Could not update table: {e}")
    return True

def display_chat_history():
    """Display chat history with newest messages at the bottom"""
    if not st.session_state.chat_history:
        st.info("Noch keine Unterhaltung gestartet. Stellen Sie eine Frage!")
        return
    
    # Create a container for the chat messages
    chat_container = st.container()
    
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message['type'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>Du:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"🕒 {message['timestamp']}")
            
            elif message['type'] == 'bot':
                confidence_class = get_confidence_class(message['confidence'])
                
                # Check if this is a clarification message
                is_clarification = message.get('clarification_mode', False)
                bot_icon = "🤔" if is_clarification else "🤖"
                bot_name = "Basti (Nachfrage)" if is_clarification else "Basti"
                
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>{bot_icon} {bot_name}:</strong> {message['content']}
                    <br>
                    <span class="confidence-badge {confidence_class}">
                        Vertrauen: {message['confidence']:.1%}
                    </span>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"🕒 {message['timestamp']}")
                
                # Show quality scores (only in AI debug mode)
                if st.session_state.debug_mode_ai and 'quality_scores' in message and message.get('quality_scores'):
                    quality_scores = message['quality_scores']
                    
                    # Get scores with default values if analysis is pending
                    chunk_coverage = quality_scores.get('chunk_coverage', None)
                    knowledge_gap = quality_scores.get('knowledge_gap', None)
                    hallucination_risk = quality_scores.get('hallucination_risk', None)
                    
                    # Determine colors based on scores
                    def get_coverage_color(score):
                        if score is None: return "#cccccc"
                        if score >= 80: return "#4CAF50"  # Green
                        if score >= 50: return "#FFC107"  # Yellow
                        return "#F44336"  # Red
                    
                    def get_gap_color(score):
                        if score is None: return "#cccccc"
                        if score <= 20: return "#4CAF50"  # Green (wenig Gap ist gut)
                        if score <= 50: return "#FFC107"  # Yellow
                        return "#FF9800"  # Orange
                    
                    def get_hallucination_color(score):
                        if score is None: return "#cccccc"
                        if score <= 20: return "#4CAF50"  # Green
                        if score <= 50: return "#FFC107"  # Yellow
                        return "#F44336"  # Red
                    
                    coverage_color = get_coverage_color(chunk_coverage)
                    gap_color = get_gap_color(knowledge_gap)
                    hallucination_color = get_hallucination_color(hallucination_risk)
                    
                    coverage_text = f"{chunk_coverage:.0f}%" if chunk_coverage is not None else "⏳ Analysiere..."
                    gap_text = f"{knowledge_gap:.0f}%" if knowledge_gap is not None else "⏳ Analysiere..."
                    hallucination_text = f"{hallucination_risk:.0f}%" if hallucination_risk is not None else "⏳ Analysiere..."
                    
                    st.markdown(f"""
                    <div style="display: flex; gap: 10px; margin: 10px 0; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 150px; background-color: {coverage_color}; padding: 10px; border-radius: 5px; color: white; text-align: center;">
                            <div style="font-size: 0.8rem; opacity: 0.9;">📊 Chunk Coverage</div>
                            <div style="font-size: 1.5rem; font-weight: bold;">{coverage_text}</div>
                        </div>
                        <div style="flex: 1; min-width: 150px; background-color: {gap_color}; padding: 10px; border-radius: 5px; color: white; text-align: center;">
                            <div style="font-size: 0.8rem; opacity: 0.9;">🔧 Knowledge Gap</div>
                            <div style="font-size: 1.5rem; font-weight: bold;">{gap_text}</div>
                        </div>
                        <div style="flex: 1; min-width: 150px; background-color: {hallucination_color}; padding: 10px; border-radius: 5px; color: white; text-align: center;">
                            <div style="font-size: 0.8rem; opacity: 0.9;">⚠️ Hallucination Risk</div>
                            <div style="font-size: 1.5rem; font-weight: bold;">{hallucination_text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show analysis details in expander if available
                    if quality_scores.get('analysis_details') and quality_scores.get('analysis_details') != 'Pending':
                        with st.expander("📋 Detaillierte Qualitäts-Analyse", expanded=False):
                            # Summary
                            st.markdown("### 📊 Zusammenfassung")
                            st.write(quality_scores.get('analysis_details', ''))
                            
                            # Coverage breakdown if available
                            if quality_scores.get('coverage_breakdown'):
                                breakdown = quality_scores['coverage_breakdown']
                                st.markdown("### 🔢 Coverage Breakdown")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Gesamt Sätze", breakdown.get('total_sentences', 'N/A'))
                                with col2:
                                    st.metric("Aus Chunks", breakdown.get('sourced_sentences', 'N/A'))
                                with col3:
                                    st.metric("Hinzugefügt", breakdown.get('added_sentences', 'N/A'))
                            
                            # Sentence-by-sentence analysis with visual separation
                            if quality_scores.get('sentence_analysis'):
                                st.markdown("### 🔍 Satz-für-Satz Analyse")
                                st.markdown("*Prüfung jeder Aussage: Stammt sie aus den Chunks oder wurde sie hinzugefügt?*")
                                
                                # Get all sources/chunks for reference
                                debug_info = message.get('debug_info', {})
                                all_chunks = debug_info.get('all_selected_chunks', [])
                                
                                for idx, analysis in enumerate(quality_scores.get('sentence_analysis', []), 1):
                                    status = analysis.get('status', 'unknown')
                                    
                                    # Define colors and icons based on status
                                    if status == 'found':
                                        bg_color = "#d4edda"  # Light green
                                        icon = "✅"
                                        status_text = "In Chunks gefunden"
                                        border_color = "#28a745"
                                    elif status == 'partial':
                                        bg_color = "#fff3cd"  # Light yellow
                                        icon = "⚠️"
                                        status_text = "Teilweise in Chunks"
                                        border_color = "#ffc107"
                                    elif status == 'not_found':
                                        bg_color = "#f8d7da"  # Light red
                                        icon = "❌"
                                        status_text = "NICHT in Chunks"
                                        border_color = "#dc3545"
                                    else:  # added
                                        bg_color = "#d1ecf1"  # Light blue
                                        icon = "➕"
                                        status_text = "Vom LLM hinzugefügt"
                                        border_color = "#17a2b8"
                                    
                                    # Get data from analysis
                                    source_chunk_name = analysis.get('source_chunk', None)
                                    chunk_quote = analysis.get('chunk_quote', None)
                                    explanation = analysis.get('explanation', 'Keine Erklärung verfügbar')
                                    answer_statement = analysis.get('answer_statement', 'N/A')
                                    
                                    # Escape HTML in text content to prevent rendering issues
                                    import html
                                    answer_statement_safe = html.escape(answer_statement)
                                    explanation_safe = html.escape(explanation)
                                    
                                    # Build chunk display section
                                    chunk_display = ""
                                    if chunk_quote and source_chunk_name:
                                        chunk_quote_safe = html.escape(chunk_quote)
                                        source_chunk_safe = html.escape(source_chunk_name)
                                        chunk_display = f"""<div style='background-color: white; padding: 10px; border-radius: 3px; margin: 10px 0; color: #000000;'>
                                            <strong style='color: #000000;'>📚 Quelle ({source_chunk_safe}):</strong><br>
                                            <em style='color: #000000;'>"{chunk_quote_safe}"</em>
                                        </div>"""
                                    
                                    # Display complete analysis box with all content in one HTML block
                                    html_content = f"""<div style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 15px; margin: 15px 0; border-radius: 5px; color: #000000;">
                                        <div style="font-weight: bold; color: #000000; margin-bottom: 10px;">
                                            {icon} Analyse #{idx} - {status_text}
                                        </div>
                                        <div style="background-color: white; padding: 10px; border-radius: 3px; margin: 10px 0; color: #000000;">
                                            <strong style="color: #000000;">📝 Aussage in der Antwort:</strong><br>
                                            <em style="color: #000000;">"{answer_statement_safe}"</em>
                                        </div>
                                        {chunk_display}
                                        <div style="margin-top: 10px; color: #000000; font-size: 0.9em;">
                                            <strong style="color: #000000;">💡 Erklärung:</strong> {explanation_safe}
                                        </div>
                                    </div>"""
                                    
                                    st.markdown(html_content, unsafe_allow_html=True)
                                    
                                    # Show full chunk in expander if available
                                    if chunk_quote and source_chunk_name:
                                        try:
                                            chunk_num = int(source_chunk_name.replace('CHUNK', '').strip()) - 1
                                            if 0 <= chunk_num < len(all_chunks):
                                                full_chunk = all_chunks[chunk_num]
                                                full_chunk_text = full_chunk.get('text', 'Chunk nicht verfügbar')
                                                chunk_speaker = full_chunk.get('speaker', 'Unknown')
                                                chunk_timestamp = full_chunk.get('timestamp', 0)
                                                
                                                with st.expander(f"🔍 Kompletten {source_chunk_name} anzeigen"):
                                                    st.markdown(f"**[{format_timestamp(chunk_timestamp)}] {chunk_speaker}**")
                                                    st.text_area(
                                                        "Vollständiger Chunk-Text",
                                                        value=full_chunk_text,
                                                        height=150,
                                                        key=f"chunk_full_{i}_{idx}",
                                                        label_visibility="collapsed"
                                                    )
                                        except (ValueError, IndexError) as e:
                                            logger.warning(f"Could not parse chunk number from {source_chunk_name}: {e}")
                                
                                st.markdown("---")
                            
                            # Detailed reasoning (legacy format)
                            if quality_scores.get('detailed_reasoning') and not quality_scores.get('sentence_analysis'):
                                st.markdown("### 🔍 Detailliertes Reasoning")
                                st.markdown(quality_scores.get('detailed_reasoning', ''))
                            
                            # Specific gaps
                            if quality_scores.get('specific_gaps'):
                                st.markdown("### 🔧 Gefüllte Wissenslücken")
                                st.info("Diese Informationen wurden vom LLM hinzugefügt:")
                                for gap in quality_scores.get('specific_gaps', []):
                                    st.write(f"• {gap}")
                            
                            # Potential hallucinations
                            if quality_scores.get('potential_hallucinations'):
                                st.markdown("### ⚠️ Potenzielle Halluzinationen")
                                st.warning("Diese Aussagen sind NICHT in den Chunks enthalten:")
                                for hall in quality_scores.get('potential_hallucinations', []):
                                    st.write(f"❌ {hall}")
                
                # Show debug information if enabled
                if st.session_state.debug_mode and 'debug_info' in message:
                    debug_info = message['debug_info']
                    basti_tone_status = "✅ Aktiviert" if debug_info.get('basti_tone', False) else "❌ Deaktiviert"
                    basti_tone_v2_status = "✅ Aktiviert" if debug_info.get('basti_tone_v2', False) else "❌ Deaktiviert"
                    clarification_status = "✅ Aktiviert" if debug_info.get('clarification_mode', False) else "❌ Deaktiviert"
                    
                    st.markdown(f"""
                    <div class="debug-info">
                        <strong>Debug Info:</strong><br>
                        • Verwendete Chunks: {debug_info.get('chunks_used', 'N/A')}<br>
                        • Gefundene Chunks: {debug_info.get('total_chunks', 'N/A')}<br>
                        • Verarbeitungszeit: {debug_info.get('processing_time', 'N/A')}s<br>
                        • Modell: {debug_info.get('model', 'N/A')}<br>
                        • Basti O-Ton: {basti_tone_status}<br>
                        • O-Ton-BASTI-AI2: {basti_tone_v2_status}<br>
                        • Nachfrage-Modus: {clarification_status}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show question strategy if iterative mode is active
                    if st.session_state.get('iterative_clarification_mode', False) and st.session_state.agent:
                        if hasattr(st.session_state.agent, 'clarification_mode'):
                            strategy = st.session_state.agent.clarification_mode.question_strategy
                            if strategy:
                                with st.expander("🎯 Fragen-Strategie"):
                                    answered_count = sum(1 for q in strategy['questions'] if q.get('answered', False))
                                    total_count = len(strategy['questions'])
                                    st.write(f"**Fortschritt:** {answered_count}/{total_count} Fragen beantwortet")
                                    st.progress(answered_count / total_count if total_count > 0 else 0)
                                    
                                    st.write("**Geplante Fragen:**")
                                    for q in strategy['questions']:
                                        status_icon = "✅" if q.get('answered', False) else "⏳"
                                        category = q.get('category', 'Allgemein')
                                        question_text = q.get('question', '')
                                        
                                        if q.get('answered', False):
                                            answer_summary = q.get('answer_found', '')
                                            st.markdown(f"{status_icon} **{category}:** {question_text}  \n*Antwort: {answer_summary}*")
                                        else:
                                            st.markdown(f"{status_icon} **{category}:** {question_text}")
                    
                    # Show sources if available (without HTML snippets)
                    if 'sources' in debug_info and debug_info['sources']:
                        with st.expander("📚 Quellen anzeigen"):
                            # Add selectbox to choose between Top 3 and All chunks
                            chunk_display_option = st.selectbox(
                                "Anzahl anzeigen:",
                                options=["Top 3", "Alle"],
                                key=f"chunk_display_{i}"
                            )
                            
                            # Get all selected chunks and used indices
                            all_chunks = debug_info.get('all_selected_chunks', debug_info['sources'])
                            used_indices = debug_info.get('used_chunk_indices', list(range(len(debug_info['sources']))))
                            
                            # Determine which chunks to display
                            if chunk_display_option == "Top 3":
                                chunks_to_display = all_chunks[:3]
                                display_start_idx = 0
                            else:
                                chunks_to_display = all_chunks
                                display_start_idx = 0
                            
                            # Display chunks with usage status
                            for j, source in enumerate(chunks_to_display, 1):
                                # Determine if this chunk was used
                                chunk_index = display_start_idx + j - 1
                                is_used = chunk_index in used_indices
                                
                                # Status badge
                                if is_used:
                                    status = "✅ Ausgewählt und genutzt"
                                    status_color = "#d4edda"  # Light green
                                else:
                                    status = "⚪ Ausgewählt, nicht genutzt"
                                    status_color = "#f8f9fa"  # Light gray
                                
                                # Clean text from HTML tags and get full text
                                clean_text = source.get('text', '')
                                # Remove the truncation marker if present
                                if clean_text.endswith('...'):
                                    clean_text = clean_text[:-3]
                                if '<' in clean_text and '>' in clean_text:
                                    import re
                                    clean_text = re.sub(r'<[^>]+>', '', clean_text)
                                
                                # Display chunk with status - reduced font size for better fit
                                st.markdown(f"""
                                <div style="background-color: {status_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px; color: #000000; font-size: 12px; line-height: 1.4;">
                                    <strong style="font-size: 13px;">{j}.</strong> <span style="font-size: 12px;">[{format_timestamp(source.get('timestamp', 0))}] {source.get('speaker', 'Unknown')}</span><br>
                                    <em style="font-size: 11px;">{status}</em><br>
                                    <span style="font-size: 12px;">{clean_text}</span>
                                </div>
                                """, unsafe_allow_html=True)

def perform_quality_analysis(message_index: int):
    """
    Performs quality analysis for a specific message in the chat history.
    Updates the message with quality scores.
    """
    if message_index >= len(st.session_state.chat_history):
        return
    
    message = st.session_state.chat_history[message_index]
    
    # Check if analysis is needed
    if not message.get('needs_analysis', False):
        return
    
    # Perform analysis
    try:
        question = message.get('original_question', '')
        answer = message.get('content', '')
        debug_info = message.get('debug_info', {})
        sources = debug_info.get('sources', [])
        
        # Convert sources to chunks format
        chunks = []
        for source in sources:
            chunks.append({
                'chunk_text': source.get('text', ''),
                'speaker': source.get('speaker', 'Unknown')
            })
        
        # Run quality analysis
        quality_scores = st.session_state.agent.analyze_answer_quality(answer, chunks, question)
        
        # Update message with scores
        st.session_state.chat_history[message_index]['quality_scores'] = quality_scores
        st.session_state.chat_history[message_index]['needs_analysis'] = False
        
        logger.info(f"Quality analysis completed for message {message_index}")
        
    except Exception as e:
        logger.error(f"Quality analysis failed: {e}")
        # Set error scores
        st.session_state.chat_history[message_index]['quality_scores'] = {
            'chunk_coverage': None,
            'knowledge_gap': None,
            'hallucination_risk': None,
            'analysis_details': f'Analyse fehlgeschlagen: {str(e)}'
        }
        st.session_state.chat_history[message_index]['needs_analysis'] = False

def process_question(question):
    """Process user question and return response"""
    if not st.session_state.agent:
        return None

    try:
        start_time = time.time()

        # Check if mock data is active
        if hasattr(st.session_state, 'mock_data_active') and st.session_state.mock_data_active:
            # Use mock data for testing
            mock_chunks = [
                {
                    "chunk_text": "Das ist ein Test-Video über Performance und Produktivität. In diesem Video sprechen wir über die wichtigsten Strategien für Unternehmer.",
                    "start_timestamp": 0.0,
                    "end_timestamp": 30.0,
                    "speaker": "Bastian",
                    "video_id": "test_video_001"
                },
                {
                    "chunk_text": "Die wichtigsten Punkte sind: Erstens, fokussiere dich auf deine Kernkompetenzen. Zweitens, eliminiere alle Ablenkungen. Drittens, baue ein starkes Team auf.",
                    "start_timestamp": 30.0,
                    "end_timestamp": 60.0,
                    "speaker": "Bastian",
                    "video_id": "test_video_001"
                },
                {
                    "chunk_text": "Performance bedeutet nicht nur harte Arbeit, sondern intelligente Arbeit. Nutze die 80/20-Regel und konzentriere dich auf die 20% der Aktivitäten, die 80% der Ergebnisse bringen.",
                    "start_timestamp": 60.0,
                    "end_timestamp": 90.0,
                    "speaker": "Bastian",
                    "video_id": "test_video_001"
                }
            ]
            
            # Build context from mock data
            context_text = "\n\n".join([chunk["chunk_text"] for chunk in mock_chunks])
            
            # Generate answer using LLM with mock context
            # Note: Mock mode doesn't support dynamic style analysis (no real chunks to analyze)
            if st.session_state.basti_tone_v2:
                # For mock mode, we can't do real style analysis, so we use a simplified approach
                st.warning("⚠️ O-Ton-BASTI-AI2 im Mock-Modus: Verwendet vereinfachten Stil (keine echte Chunk-Analyse möglich)")
                response = st.session_state.agent._generate_answer(question, context_text)
            elif st.session_state.basti_tone:
                basti_system_prompt = """### Tone-of-Voice-Leitfaden „High-Energy Unternehmer-Coach"

Verwende beim Text-Generieren konsequent die folgenden Stilregeln – sie bilden *den* Ton, mit dem die Videos kommunizieren:

1. **Adresse & Haltung**  
   * Sprich die Leserin/den Leser immer direkt mit **„du"** an.  
   * Verwende eine **motivierende, coachende Haltung** – als würdest du einem Freund oder einer Freundin helfen, der/die gerade vor einer wichtigen Entscheidung steht.  
   * Sei **ermutigend, aber ehrlich** – zeige auf, was möglich ist, aber verschweige nicht die Herausforderungen.

2. **Sprache & Stil**  
   * **Kurze, prägnante Sätze** – vermeide Schachtelsätze und komplizierte Konstruktionen.  
   * **Aktive Formulierungen** – „Du entscheidest" statt „Es wird entschieden".  
   * **Konkrete, bildhafte Sprache** – verwende Metaphern und Beispiele aus dem Alltag.  
   * **Direkte Ansprache** – „Stell dir vor..." oder „Hier ist der Deal..."  

3. **Emotionale Tonalität**  
   * **Energiegeladen, aber nicht übertrieben** – du bist motiviert, aber nicht aufdringlich.  
   * **Vertrauensvoll** – du weißt, wovon du sprichst, und das spürst du auch.  
   * **Lösungsorientiert** – fokussiere dich auf das, was funktioniert, nicht auf Probleme.  

4. **Strukturelle Elemente**  
   * **Klare Gliederung** – verwende Absätze, Aufzählungen oder kurze Zwischenüberschriften.  
   * **Handlungsaufforderungen** – gib konkrete, umsetzbare Tipps.  
   * **Fragen einbauen** – „Was denkst du?" oder „Wie fühlst du dich dabei?"  

5. **Beispiele für den richtigen Ton**  
   * ✅ **Richtig:** „Du stehst vor einer großen Entscheidung – und das ist gut so! Hier ist, wie du sie meisterst..."  
   * ✅ **Richtig:** „Stell dir vor, du könntest deine Zeit so nutzen, dass du mehr erreichen und trotzdem entspannter leben könntest. Klingt gut? Dann lass uns das angehen!"  
   * ❌ **Falsch:** „Es ist wichtig, dass man seine Zeit effizient nutzt." (zu passiv, zu allgemein)  

6. **Wichtige No-Gos**  
   * **Keine Floskeln** – vermeide Phrasen wie „am Ende des Tages" oder „es ist, was es ist".  
   * **Keine Übertreibungen** – „revolutionär" oder „bahnbrechend" nur, wenn es wirklich stimmt.  
   * **Keine passiven Formulierungen** – „es wird empfohlen" → „ich empfehle dir".  

Antworte jetzt in diesem Ton und Stil auf die Frage des Nutzers."""

                # Use custom system prompt for Basti tone
                response = st.session_state.agent._generate_answer(question, context_text, basti_system_prompt)
            else:
                # Use default system prompt
                response = st.session_state.agent._generate_answer(question, context_text)

            processing_time = time.time() - start_time

            # Prepare debug info
            mock_sources = [{"text": chunk["chunk_text"], "timestamp": chunk["start_timestamp"], "speaker": chunk["speaker"]} for chunk in mock_chunks]
            debug_info = {
                'chunks_used': len(mock_chunks),
                'total_chunks': len(mock_chunks),
                'processing_time': f"{processing_time:.2f}",
                'model': 'gpt-4o-mini',
                'sources': mock_sources,
                'all_selected_chunks': mock_sources,
                'used_chunk_indices': list(range(len(mock_chunks))),
                'basti_tone': st.session_state.basti_tone,
                'basti_tone_v2': st.session_state.basti_tone_v2
            }

            # Only perform quality analysis if AI debug mode is active AND chunks were used
            # For mock mode, always allow analysis (no iterative mode check needed)
            needs_analysis = st.session_state.debug_mode_ai and len(mock_chunks) > 0
            
            return {
                'answer': response,
                'confidence': 0.85,  # High confidence for mock data
                'debug_info': debug_info,
                'original_question': question,
                'needs_analysis': needs_analysis,
                'quality_scores': {  # Placeholder scores
                    'chunk_coverage': None,
                    'knowledge_gap': None,
                    'hallucination_risk': None,
                    'analysis_details': 'Pending'
                } if needs_analysis else None
            }

        # Basti O-Ton System Prompt
        basti_system_prompt = """### Tone-of-Voice-Leitfaden „High-Energy Unternehmer-Coach"

Verwende beim Text-Generieren konsequent die folgenden Stilregeln – sie bilden *den* Ton, mit dem die Videos kommunizieren:

1. **Adresse & Haltung**  
   * Sprich die Leserin/den Leser immer direkt mit **„du"** an.  
   * Klinge wie ein erfahrener, leicht rebellischer Performance-Coach: fordernd, gnadenlos ehrlich, zugleich bestärkend.

2. **Satzrhythmus**  
   * Wechsele zwischen kurzen Schlagzeilen-Sätzen („Mach's jetzt.") und dichten Aufzählungen.  
   * Setze Imperative, Tempo-Marker („sofort", „jetzt", „zack") und Zwischenrufe („Boom!") großzügig ein.

3. **Wortwahl**  
   * Kombiniere **Kampf-/Gewalt- und Sieger-Metaphern** („dominiere", „zerstöre Blockaden") mit **Business-Jargon** („KPIs", „skalieren") und **Psycho-Vokabular** („limbisches System", „Dopaminfalle").  
   * Streu **umgangssprachliche Kraftausdrücke** sparsam, aber punktgenau ein („Bullshit", „Scheiße"), um Nachdruck zu verleihen.  
   * Erlaube englische Fach- und Szenebegriffe (Denglisch) – sie sollen modern wirken.

4. **Rhetorik & Dramaturgie**  
   * Beginne häufig mit einer **Alarm-These** oder provokanten Frage, liefere dann **klare Nutzenversprechen**.  
   * Verwende nummerierte Fahrpläne („Erstens … zweitens …"), Listen mit Sofort-Hacks und direkte Handlungsaufforderungen.  
   * Unterlege Aussagen gern mit **konkreten Zahlen oder Studien-Verweisen** („30 % schlechtere Entscheidungen bei < 6 h Schlaf").

5. **Emotionalisierung**  
   * Trigger starke Gefühle: Angst vor Stillstand, Lust auf Sieg, Stolz auf Umsetzung.  
   * Stell Probleme als existenziell dar („Angst macht dich weich"), aber gib stets eine umsetzbare Lösung.

6. **Ton-Nuancen nach Bedarf**  
   * **Wissenschaftlich-warnend** (bei Daten/Studien): sachliche Belege + dringliche Mahnung.  
   * **Locker-praktisch** (bei Tools/Tutorials): Kumpelton, Humor, Live-Mitmach-Instruktionen.  
   * **Militant-motivierend** (bei Mindset): martialische Bilder, „No-Excuses"-Attitüde.

7. **Form**  
   * Benutze Fettdruck oder Emojis sparsam, nur zur Akzentuierung.  
   * Vermeide lange Theorie-Absätze ohne Action-Ableitung – jede Erkenntnis endet in einer klaren Aufgabe.

> **Kurzform des Tons (Merksatz):**  
> *„Dringlicher, hype-geladener Performance-Coach – aggressiv motivierend, wissenschaftlich untermauert, derb-kumpelhaft."*

Antworte jetzt in diesem Ton und Stil auf die Frage des Nutzers."""
        
        # Process question based on selected tone mode
        # Priority: O-Ton-BASTI-AI2 > Basti O-Ton > Default
        # Pass use_dynamic_style and creativity_level to agent
        creativity_level = st.session_state.creativity_level
        
        if st.session_state.basti_tone_v2:
            # Use dynamic style mode (O-Ton-BASTI-AI2)
            logger.info(f"Using O-Ton-BASTI-AI2 mode (dynamic style) with creativity {creativity_level}")
            response = st.session_state.agent.ask_question(
                question, 
                use_dynamic_style=True,
                force_dynamic_style=True,  # Force for iterative final answer too
                creativity_level=creativity_level
            )
        elif st.session_state.basti_tone:
            # Use custom system prompt for Basti tone (original mode)
            logger.info(f"Using Basti O-Ton mode (static) with creativity {creativity_level}")
            response = st.session_state.agent.ask_question(
                question, 
                system_prompt=basti_system_prompt,
                creativity_level=creativity_level
            )
        else:
            # Use default system prompt
            logger.info(f"Using default mode with creativity {creativity_level}")
            response = st.session_state.agent.ask_question(
                question,
                creativity_level=creativity_level
            )
        
        processing_time = time.time() - start_time
        
        # Prepare debug info
        debug_info = {
            'chunks_used': response.get('context_chunks_used', 0),
            'total_chunks': response.get('total_chunks_found', 0),
            'processing_time': f"{processing_time:.2f}",
            'model': 'gpt-4o-mini',
            'sources': response.get('sources', []),
            'all_selected_chunks': response.get('all_selected_chunks', []),
            'used_chunk_indices': response.get('used_chunk_indices', []),
            'basti_tone': st.session_state.basti_tone,
            'basti_tone_v2': st.session_state.basti_tone_v2,
            'clarification_mode': response.get('clarification_mode', False)
        }
        
        # Only perform quality analysis if AI debug mode is active AND chunks were used
        # AND it's not a clarification question (only analyze final answers)
        is_clarification = response.get('clarification_mode', False)
        is_final_answer = response.get('final_answer', False)
        is_iterative = response.get('iterative_mode', False)
        
        # Only analyze if: AI debug mode + chunks used + (not iterative OR is final answer)
        needs_analysis = (st.session_state.debug_mode_ai and 
                         response.get('context_chunks_used', 0) > 0 and
                         (not is_iterative or is_final_answer))
        
        return {
            'answer': response['answer'],
            'confidence': response['confidence'],
            'debug_info': debug_info,
            'original_question': question,
            'needs_analysis': needs_analysis,
            'quality_scores': {  # Placeholder scores (only filled if needs_analysis is True)
                'chunk_coverage': None,
                'knowledge_gap': None,
                'hallucination_risk': None,
                'analysis_details': 'Pending'
            } if needs_analysis else None,
            # Pass through important flags from agent response
            'final_answer': response.get('final_answer', False),
            'iterative_mode': response.get('iterative_mode', False),
            'clarification_mode': response.get('clarification_mode', False),
            'context_chunks_used': response.get('context_chunks_used', 0),
            'total_chunks_found': response.get('total_chunks_found', 0)
        }
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        st.error(f"Fehler beim Verarbeiten der Frage: {e}")
        return None

def run_automatic_iterative_test():
    """
    Führt einen vollautomatischen iterativen Test durch.
    Stellt eine Frage und beantwortet alle Nachfragen automatisch.
    """
    import time
    
    # Test configuration
    initial_question = "Ich möchte abnehmen"
    max_iterations = 10  # Safety limit
    
    # Automatic answers for common questions
    auto_answers = {
        "gewicht": "Ich möchte 10 kg abnehmen",
        "kg": "10 kg",
        "kilo": "10 kg",
        "sport": "Ich mache aktuell 2 mal pro Woche Sport, hauptsächlich Joggen",
        "training": "2 mal pro Woche Joggen, jeweils 30 Minuten",
        "ernährung": "Ich esse relativ normal, viel Pasta und Brot. Abends oft Fast Food",
        "essen": "Morgens Müsli, mittags in der Kantine, abends oft Pizza oder Burger",
        "zeitrahmen": "Ich möchte das in 3 Monaten schaffen",
        "wann": "In 3 Monaten",
        "monat": "3 Monate",
        "versucht": "Ich habe schon Low-Carb probiert, aber nicht durchgehalten",
        "diät": "Low-Carb habe ich versucht, aber nach 2 Wochen aufgegeben",
        "hindernis": "Mein größtes Problem ist der Stress bei der Arbeit und Heißhunger abends",
        "problem": "Stress und Heißhunger abends vor dem Fernseher",
        "budget": "Ich kann etwa 100 Euro pro Monat für gesundes Essen und Fitness ausgeben",
        "geld": "100 Euro im Monat",
        "alter": "Ich bin 35 Jahre alt",
        "größe": "Ich bin 1,80m groß",
        "gewohnheit": "Ich sitze viel im Büro und bewege mich wenig im Alltag",
        "alltag": "Bürojob, 8 Stunden sitzen, wenig Bewegung",
        "schlaf": "Ich schlafe etwa 6-7 Stunden pro Nacht",
        "wasser": "Ich trinke etwa 1,5 Liter Wasser am Tag",
        "motivation": "Ich möchte mich wieder wohler fühlen und gesünder leben"
    }
    
    # Save original settings
    original_iterative_mode = st.session_state.get('iterative_clarification_mode', False)
    original_debug_mode = st.session_state.get('debug_mode', False)
    original_debug_mode_ai = st.session_state.get('debug_mode_ai', False)
    original_chat_history = st.session_state.get('chat_history', []).copy()
    
    try:
        # Enable iterative mode and all debug modes for the test
        st.session_state.iterative_clarification_mode = True
        st.session_state.debug_mode = True
        st.session_state.debug_mode_ai = True
        
        if st.session_state.agent:
            st.session_state.agent.toggle_iterative_clarification_mode(True)
        
        # Clear history for clean test
        st.session_state.chat_history = []
        if st.session_state.agent:
            st.session_state.agent.clear_history()
        
        logger.info("🔧 Test-Einstellungen: Alle Debug-Modi aktiviert, Historie gelöscht")
        
        logger.info(f"🧪 Starting automatic iterative test with question: '{initial_question}'")
        
        test_result = {
            'initial_question': initial_question,
            'iterations': [],
            'final_answer': None,
            'final_confidence': 0.0,
            'num_iterations': 0,
            'total_duration': 0.0
        }
        
        start_time = time.time()
        current_question = initial_question
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            iteration_start = time.time()
            
            logger.info(f"🔄 Iteration {iteration}: Asking '{current_question}'")
            
            # Ask question
            response = process_question(current_question)
            
            if not response:
                logger.error("❌ No response received")
                break
            
            iteration_duration = time.time() - iteration_start
            
            # Check if this is the final answer
            debug_info = response.get('debug_info', {})
            # In iterative mode, check for 'final_answer' flag
            final_answer_flag = response.get('final_answer', False)
            iterative_mode_flag = response.get('iterative_mode', False)
            clarification_mode_flag = response.get('clarification_mode', False)
            
            logger.info(f"🔍 Response flags: final_answer={final_answer_flag}, iterative_mode={iterative_mode_flag}, clarification_mode={clarification_mode_flag}")
            
            is_final = final_answer_flag
            
            if is_final:
                # Final answer received
                logger.info(f"✅ Final answer received after {iteration} iterations")
                test_result['final_answer'] = response['answer']
                test_result['final_confidence'] = response['confidence']
                test_result['num_iterations'] = iteration
                test_result['context_chunks_used'] = response.get('context_chunks_used', 0)
                test_result['total_chunks_found'] = response.get('total_chunks_found', 0)
                test_result['debug_info'] = debug_info
                
                # Trigger quality analysis if debug_mode_ai is enabled
                if st.session_state.debug_mode_ai and response.get('context_chunks_used', 0) > 0:
                    logger.info("🤖 Starting AI quality analysis for final answer...")
                    
                    # Get chunks from debug info
                    sources = debug_info.get('sources', [])
                    chunks = []
                    for source in sources:
                        chunks.append({
                            'chunk_text': source.get('text', ''),
                            'speaker': source.get('speaker', 'Unknown')
                        })
                    
                    # Perform quality analysis
                    try:
                        quality_scores = st.session_state.agent.analyze_answer_quality(
                            response['answer'], 
                            chunks, 
                            initial_question
                        )
                        test_result['quality_scores'] = quality_scores
                        logger.info(f"✅ Quality analysis completed: Coverage={quality_scores.get('chunk_coverage')}%")
                    except Exception as e:
                        logger.error(f"❌ Quality analysis failed: {e}")
                        test_result['quality_scores'] = {
                            'chunk_coverage': None,
                            'knowledge_gap': None,
                            'hallucination_risk': None,
                            'analysis_details': f'Analyse fehlgeschlagen: {str(e)}'
                        }
                
                break
            else:
                # This is a clarification question - find automatic answer
                bot_question = response['answer']
                
                # Find matching auto-answer based on keywords in bot question
                auto_answer = None
                bot_question_lower = bot_question.lower()
                
                for keyword, answer in auto_answers.items():
                    if keyword in bot_question_lower:
                        auto_answer = answer
                        logger.info(f"✅ Found auto-answer for keyword '{keyword}': {answer}")
                        break
                
                # Fallback answer if no match found
                if not auto_answer:
                    auto_answer = "Das kann ich so pauschal nicht sagen, aber ich möchte mein Bestes geben."
                    logger.warning(f"⚠️ No matching auto-answer found, using fallback")
                
                test_result['iterations'].append({
                    'bot_question': bot_question,
                    'auto_answer': auto_answer,
                    'duration': iteration_duration,
                    'confidence': response['confidence']
                })
                
                # Set next question to the auto-answer
                current_question = auto_answer
        
        test_result['total_duration'] = time.time() - start_time
        
        # Check if we got a final answer
        if test_result['final_answer'] is None:
            logger.warning(f"⚠️ Test ended without final answer after {iteration} iterations")
            if iteration >= max_iterations:
                test_result['final_answer'] = "Test erreichte maximale Anzahl an Iterationen ohne finale Antwort."
            else:
                test_result['final_answer'] = "Test wurde abgebrochen - keine finale Antwort erhalten."
            test_result['final_confidence'] = 0.0
            test_result['num_iterations'] = iteration
        else:
            logger.info(f"🎉 Automatic test completed in {test_result['total_duration']:.2f}s with {test_result['num_iterations']} iterations")
        
        return test_result
        
    except Exception as e:
        logger.error(f"❌ Automatic test failed: {e}", exc_info=True)
        return None
        
    finally:
        # Restore original settings
        st.session_state.iterative_clarification_mode = original_iterative_mode
        st.session_state.debug_mode = original_debug_mode
        st.session_state.debug_mode_ai = original_debug_mode_ai
        
        if st.session_state.agent:
            st.session_state.agent.toggle_iterative_clarification_mode(original_iterative_mode)


def test_connections():
    """Test database and API connections."""
    test_results = {
        'openai': False,
        'supabase': False,
        'database_query': False,
        'chunks_found': 0,
        'error_messages': []
    }
    
    try:
        # Test OpenAI connection
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Simple test request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        test_results['openai'] = True
    except Exception as e:
        test_results['error_messages'].append(f"OpenAI Error: {str(e)}")
    
    try:
        # Test Supabase connection
        from supabase import create_client, Client
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SECRET_KEY')
        
        if url and key:
            supabase: Client = create_client(url, key)
            
            # Test database query
            result = supabase.table('video_chunks').select('*').limit(1).execute()
            test_results['supabase'] = True
            test_results['database_query'] = True
            
            # Count total chunks
            count_result = supabase.table('video_chunks').select('id', count='exact').execute()
            test_results['chunks_found'] = count_result.count if count_result.count else 0
        else:
            test_results['error_messages'].append("Supabase credentials not found")
    except Exception as e:
        test_results['error_messages'].append(f"Supabase Error: {str(e)}")
    
    return test_results


def main():
    """Main Streamlit application"""

    initialize_session_state()

    # Check if there are any pending quality analyses
    # This runs BEFORE displaying the UI to update scores
    if st.session_state.agent:
        for i, message in enumerate(st.session_state.chat_history):
            if message.get('type') == 'bot' and message.get('needs_analysis', False):
                logger.info(f"Found pending quality analysis for message {i}, performing now...")
                perform_quality_analysis(i)
                rerun_app()

    logo_svg = load_logo_svg()

    header_cols = st.columns([1.4, 3, 1.4])
    with header_cols[0]:
        if logo_svg:
            st.markdown(f'<div class="logo-container">{logo_svg}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="logo-container">Umsetzer</div>', unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown('<div class="app-title">Umsetzer · BastiAI</div>', unsafe_allow_html=True)
        st.markdown('<div class="app-subtitle">Version 3.0</div>', unsafe_allow_html=True)
    with header_cols[2]:
        menu_label = "✖ Menü schließen" if st.session_state.menu_open else "☰ Menü öffnen"
        if st.button(menu_label, key="menu_toggle"):
            st.session_state.menu_open = not st.session_state.menu_open
            rerun_app()

    if st.session_state.menu_open:
        render_control_panel()

    if not initialize_agent():
        st.stop()

    apply_selected_chunk_table()

    active_table = st.session_state.get('selected_chunk_table', 'video_chunks_video_optimized')
    table_labels = {
        "video_chunks": "Semantic (Standard)",
        "video_chunks_recursive": "Recursive",
        "video_chunks_video_optimized": "Video Optimized",
        "video_chunks_fixed": "Fixed",
    }
    table_label = table_labels.get(active_table, active_table)

    if st.session_state.chunk_table_error:
        st.markdown(
            f'<div class="status-strip">⚠️ Fehler beim Setzen der Tabelle: {st.session_state.chunk_table_error}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="status-strip">📊 Aktive Datenbasis: <strong>{table_label}</strong> ({active_table})</div>',
            unsafe_allow_html=True,
        )

    if hasattr(st.session_state, 'test_result') and st.session_state.test_result:
        st.markdown("## 📊 Test-Ergebnisse: Vollautomatischer Iterativer Test")
        test_result = st.session_state.test_result

        st.markdown("### 🎯 Test-Zusammenfassung")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ursprüngliche Frage", test_result['initial_question'][:30] + "...")
        with col2:
            st.metric("Anzahl Nachfragen", test_result['num_iterations'])
        with col3:
            st.metric("Test-Dauer", f"{test_result['total_duration']:.2f}s")

        st.markdown("### 🔄 Iterationsverlauf")
        for i, iteration in enumerate(test_result['iterations'], 1):
            with st.container():
                st.markdown(f"**Iteration {i}:**")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.info(f"🤖 **Bot fragt:** {iteration['bot_question']}")
                with col2:
                    st.success(f"👤 **Auto-Antwort:** {iteration['auto_answer']}")

                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.caption(f"⏱️ Dauer: {iteration['duration']:.2f}s")
                with metric_col2:
                    st.caption(f"📊 Confidence: {iteration.get('confidence', 0.0):.1%}")

                st.markdown("---")

        st.markdown("### ✅ Finale Antwort")
        st.success(test_result['final_answer'])

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Confidence", f"{test_result['final_confidence']:.1%}")
        with metric_col2:
            if 'context_chunks_used' in test_result:
                st.metric("Chunks verwendet", test_result['context_chunks_used'])
        with metric_col3:
            if 'total_chunks_found' in test_result:
                st.metric("Chunks gefunden", test_result['total_chunks_found'])

        if 'debug_info' in test_result and test_result['debug_info']:
            with st.expander("🔍 Debug-Informationen", expanded=False):
                debug_info = test_result['debug_info']

                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Verarbeitungsdetails:**")
                    st.write(f"• Modell: {debug_info.get('model', 'N/A')}")
                    st.write(f"• Verarbeitungszeit: {debug_info.get('processing_time', 'N/A')}s")
                    st.write(f"• Chunks verwendet: {debug_info.get('chunks_used', 'N/A')}")
                    st.write(f"• Chunks gefunden: {debug_info.get('total_chunks', 'N/A')}")

                with col2:
                    st.write("**Modi:**")
                    basti_tone_status = "✅ Aktiv" if debug_info.get('basti_tone', False) else "❌ Inaktiv"
                    basti_tone_v2_status = "✅ Aktiv" if debug_info.get('basti_tone_v2', False) else "❌ Inaktiv"
                    clarification = "✅ Aktiv" if debug_info.get('clarification_mode', False) else "❌ Inaktiv"
                    st.write(f"• Basti O-Ton: {basti_tone_status}")
                    st.write(f"• O-Ton-BASTI-AI2: {basti_tone_v2_status}")
                    st.write(f"• Nachfrage-Modus: {clarification}")

                if 'sources' in debug_info and debug_info['sources']:
                    st.markdown("**📚 Verwendete Quellen:**")
                    for i, source in enumerate(debug_info['sources'][:5], 1):
                        timestamp = source.get('timestamp', 0)
                        minutes = int(timestamp // 60)
                        seconds = int(timestamp % 60)
                        speaker = source.get('speaker', 'Unknown')
                        text = source.get('text', '')[:100]
                        st.markdown(f"{i}. **[{minutes:02d}:{seconds:02d}] {speaker}:** {text}...")

        if 'quality_scores' in test_result and test_result['quality_scores']:
            with st.expander("🤖 AI-Qualitätsanalyse", expanded=False):
                quality_scores = test_result['quality_scores']

                col1, col2, col3 = st.columns(3)
                with col1:
                    coverage = quality_scores.get('chunk_coverage', 0)
                    st.metric("📊 Chunk Coverage", f"{coverage:.1f}%")
                with col2:
                    gap = quality_scores.get('knowledge_gap', 0)
                    st.metric("🔧 Knowledge Gap", f"{gap:.1f}%")
                with col3:
                    hallucination = quality_scores.get('hallucination_risk', 0)
                    st.metric("⚠️ Hallucination Risk", f"{hallucination:.1f}%")

                if quality_scores.get('analysis_details'):
                    st.markdown("**Zusammenfassung:**")
                    st.info(quality_scores['analysis_details'])

                if quality_scores.get('detailed_reasoning'):
                    st.markdown("**Detailliertes Reasoning:**")
                    st.text_area("", quality_scores['detailed_reasoning'], height=200, disabled=True)

        button_col1, button_col2 = st.columns(2)
        with button_col1:
            if st.button("📋 In Chat anzeigen", use_container_width=True):
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []

                st.session_state.chat_history.append({
                    'type': 'user',
                    'content': test_result['initial_question'],
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                })

                st.session_state.chat_history.append({
                    'type': 'bot',
                    'content': test_result['final_answer'],
                    'confidence': test_result['final_confidence'],
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'debug_info': test_result.get('debug_info', {}),
                    'quality_scores': test_result.get('quality_scores', {})
                })

                st.success("✅ Test-Ergebnis zum Chat hinzugefügt!")
                rerun_app()

        with button_col2:
            if st.button("🗑️ Test-Ergebnisse löschen", use_container_width=True):
                del st.session_state.test_result
                rerun_app()

    st.markdown("### 💬 Chat")
    display_chat_history()

    form_submitted = False
    question = ""
    st.markdown('<div class="chat-input-card">', unsafe_allow_html=True)
    with st.form(key="question_form", clear_on_submit=True):
        question = st.text_area(
            "Stellen Sie eine Frage zu den Video-Inhalten:",
            placeholder="Z.B. Was ist das Hauptthema des Videos?",
            key="question_input",
            label_visibility="collapsed",
            height=140,
        )
        submit_columns = st.columns([5, 1.2])
        with submit_columns[1]:
            form_submitted = st.form_submit_button("Senden")
    st.markdown('</div>', unsafe_allow_html=True)

    if form_submitted:
        if question.strip():
            user_message = {
                'type': 'user',
                'content': question,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.chat_history.append(user_message)

            with st.spinner("Suche nach relevanten Inhalten..."):
                response = process_question(question)

            if response:
                bot_message = {
                    'type': 'bot',
                    'content': response['answer'],
                    'confidence': response['confidence'],
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'debug_info': response.get('debug_info', {}),
                    'clarification_mode': response.get('clarification_mode', False),
                    'original_question': response.get('original_question', question),
                    'needs_analysis': response.get('needs_analysis', False),
                    'quality_scores': response.get('quality_scores', {})
                }
                st.session_state.chat_history.append(bot_message)

            rerun_app()
        else:
            note_block("⚠️ Bitte geben Sie eine Frage ein.")

    st.markdown(
        """
        <div style="text-align: center; color: rgba(255, 255, 255, 0.55); font-size: 0.8rem; letter-spacing: 0.32em; margin-top: 3rem;">
            BastiAI · Powered by Umsetzer · Version 3.0
        </div>
        """,
        unsafe_allow_html=True,
    )



if __name__ == "__main__":
    main()
