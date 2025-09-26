"""
Streamlit Web Interface for Video Chat Agent
"""

import streamlit as st
import logging
from pathlib import Path
import sys
from datetime import datetime
import time

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agent.mini_chat_agent import MiniChatAgent
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="BastiAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #ff6b6b;
    }
    .bot-message {
        background-color: #e8f4fd;
        border-left-color: #1f77b4;
    }
    .debug-info {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
        font-size: 0.8rem;
    }
    .confidence-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .confidence-high {
        background-color: #d4edda;
        color: #155724;
    }
    .confidence-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .confidence-low {
        background-color: #f8d7da;
        color: #721c24;
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
    if 'basti_tone' not in st.session_state:
        st.session_state.basti_tone = True

def initialize_agent():
    """Initialize the chat agent"""
    if st.session_state.agent is None:
        try:
            with st.spinner("Initialisiere Chat Agent..."):
                st.session_state.agent = MiniChatAgent()
            st.success("Chat Agent erfolgreich initialisiert!")
            return True
        except Exception as e:
            st.error(f"Fehler beim Initialisieren des Chat Agents: {e}")
            logger.error(f"Agent initialization failed: {e}")
            return False
    return True

def display_chat_history():
    """Display chat history"""
    if not st.session_state.chat_history:
        st.info("Noch keine Unterhaltung gestartet. Stellen Sie eine Frage!")
        return
    
    for i, message in enumerate(st.session_state.chat_history):
        if message['type'] == 'user':
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>Du:</strong> {message['content']}
                <br><small>{message['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        elif message['type'] == 'bot':
            confidence_class = get_confidence_class(message['confidence'])
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🤖 Basti:</strong> {message['content']}
                <br>
                <span class="confidence-badge {confidence_class}">
                    Vertrauen: {message['confidence']:.1%}
                </span>
                <br><small>{message['timestamp']}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Show debug information if enabled
            if st.session_state.debug_mode and 'debug_info' in message:
                debug_info = message['debug_info']
                basti_tone_status = "✅ Aktiviert" if debug_info.get('basti_tone', False) else "❌ Deaktiviert"
                st.markdown(f"""
                <div class="debug-info">
                    <strong>Debug Info:</strong><br>
                    • Verwendete Chunks: {debug_info.get('chunks_used', 'N/A')}<br>
                    • Gefundene Chunks: {debug_info.get('total_chunks', 'N/A')}<br>
                    • Verarbeitungszeit: {debug_info.get('processing_time', 'N/A')}s<br>
                    • Modell: {debug_info.get('model', 'N/A')}<br>
                    • Basti O-Ton: {basti_tone_status}
                </div>
                """, unsafe_allow_html=True)
                
                # Show sources if available
                if 'sources' in debug_info and debug_info['sources']:
                    with st.expander("📚 Quellen anzeigen"):
                        for j, source in enumerate(debug_info['sources'][:3], 1):
                            st.write(f"**{j}.** [{format_timestamp(source.get('timestamp', 0))}] "
                                   f"{source.get('speaker', 'Unknown')}: "
                                   f"{source.get('text', '')[:200]}...")

def process_question(question):
    """Process user question and return response"""
    if not st.session_state.agent:
        return None
    
    try:
        start_time = time.time()
        
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
        
        # Process question with or without Basti tone
        if st.session_state.basti_tone:
            # Use custom system prompt for Basti tone
            response = st.session_state.agent.ask_question(question, system_prompt=basti_system_prompt)
        else:
            # Use default system prompt
            response = st.session_state.agent.ask_question(question)
        
        processing_time = time.time() - start_time
        
        # Prepare debug info
        debug_info = {
            'chunks_used': response.get('context_chunks_used', 0),
            'total_chunks': response.get('total_chunks_found', 0),
            'processing_time': f"{processing_time:.2f}",
            'model': 'gpt-4o-mini',
            'sources': response.get('sources', []),
            'basti_tone': st.session_state.basti_tone
        }
        
        return {
            'answer': response['answer'],
            'confidence': response['confidence'],
            'debug_info': debug_info
        }
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        st.error(f"Fehler beim Verarbeiten der Frage: {e}")
        return None

def main():
    """Main Streamlit application"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 BastiAI</h1>', unsafe_allow_html=True)
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Einstellungen")
        
        # Debug mode toggle
        debug_mode = st.checkbox(
            "Debug-Modus aktivieren", 
            value=st.session_state.debug_mode,
            help="Zeigt zusätzliche Informationen wie Quellen und Verarbeitungszeiten"
        )
        st.session_state.debug_mode = debug_mode
        
        # Basti O-Ton toggle
        basti_tone = st.checkbox(
            "Basti O-Ton aktivieren", 
            value=st.session_state.basti_tone,
            help="Aktiviert Bastians charakteristischen Performance-Coach Ton für die Antworten (Standard: aktiviert)"
        )
        st.session_state.basti_tone = basti_tone
        
        # Check URL parameters for debug mode
        query_params = st.query_params
        if 'debug' in query_params:
            url_debug = query_params['debug'].lower() in ['true', '1', 'yes']
            if url_debug != st.session_state.debug_mode:
                st.session_state.debug_mode = url_debug
                st.rerun()
        
        st.divider()
        
        # Agent status
        st.subheader("🤖 Basti Status")
        if st.session_state.agent:
            st.success("✅ Basti bereit")
        else:
            st.warning("⚠️ Basti nicht initialisiert")
        
        # Clear chat history
        if st.button("🗑️ Chat-Verlauf löschen"):
            st.session_state.chat_history = []
            if st.session_state.agent:
                st.session_state.agent.clear_history()
            st.rerun()
        
        st.divider()
        
        # Information
        st.subheader("ℹ️ Informationen")
        st.info("""
        **Verfügbare Funktionen:**
        - Fragen zu Video-Inhalten stellen
        - Vertrauens-Score für Antworten
        - Debug-Modus für detaillierte Infos
        - Chat-Verlauf
        """)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Initialize agent if not done
        if not initialize_agent():
            st.stop()
        
        # Chat interface
        st.subheader("💬 Chat")
        
        # Question input
        question = st.text_input(
            "Stellen Sie eine Frage zu den Video-Inhalten:",
            placeholder="z.B. Was ist das Hauptthema des Videos?",
            key="question_input"
        )
        
        # Process button
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("🚀 Senden", type="primary"):
                if question.strip():
                    # Add user message to history
                    user_message = {
                        'type': 'user',
                        'content': question,
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    }
                    st.session_state.chat_history.append(user_message)
                    
                    # Process question
                    with st.spinner("Suche nach relevanten Inhalten..."):
                        response = process_question(question)
                    
                    if response:
                        # Add bot response to history
                        bot_message = {
                            'type': 'bot',
                            'content': response['answer'],
                            'confidence': response['confidence'],
                            'timestamp': datetime.now().strftime("%H:%M:%S"),
                            'debug_info': response['debug_info']
                        }
                        st.session_state.chat_history.append(bot_message)
                        
                        # Rerun to update display
                        st.rerun()
                    else:
                        st.error("Konnte keine Antwort generieren.")
                else:
                    st.warning("Bitte geben Sie eine Frage ein.")
        
        with col_btn2:
            if st.button("🔄 Aktualisieren"):
                st.rerun()
    
    with col2:
        # Statistics
        st.subheader("📊 Statistiken")
        
        total_messages = len(st.session_state.chat_history)
        user_messages = len([m for m in st.session_state.chat_history if m['type'] == 'user'])
        bot_messages = len([m for m in st.session_state.chat_history if m['type'] == 'bot'])
        
        st.metric("Gesamt Nachrichten", total_messages)
        st.metric("Fragen gestellt", user_messages)
        st.metric("Antworten erhalten", bot_messages)
        
        if bot_messages > 0:
            avg_confidence = sum([m['confidence'] for m in st.session_state.chat_history if m['type'] == 'bot']) / bot_messages
            st.metric("Ø Vertrauen", f"{avg_confidence:.1%}")
    
    # Display chat history
    st.divider()
    display_chat_history()
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        BastiAI - Powered by OpenAI & Supabase
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
