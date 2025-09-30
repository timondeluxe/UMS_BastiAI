"""
Mini Chat Agent for video content retrieval and Q&A
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import re

from openai import OpenAI
from config.settings import settings
from src.embedding.embedding_generator import VideoProcessor


logger = logging.getLogger(__name__)


class ClarificationMode:
    """Nachfrage-Modus für unspezifische Fragen"""
    
    def __init__(self, openai_client, video_processor):
        self.openai_client = openai_client
        self.video_processor = video_processor
        self.clarification_history = []
        
    def is_question_too_vague(self, question: str) -> bool:
        """Erkennt, ob eine Frage zu unspezifisch ist"""
        
        # Typische unspezifische Muster
        vague_patterns = [
            r"ich möchte (.*)",  # "ich möchte abnehmen"
            r"ich will (.*)",     # "ich will mehr Leads"
            r"ich brauche (.*)",  # "ich brauche Hilfe"
            r"wie kann ich (.*)", # "wie kann ich erfolgreich sein"
            r"was soll ich (.*)", # "was soll ich tun"
            r"hilf mir (.*)",     # "hilf mir"
            r"ich habe ein problem", # "ich habe ein Problem"
            r"ich weiß nicht (.*)", # "ich weiß nicht was"
        ]
        
        question_lower = question.lower().strip()
        
        # Prüfe auf unspezifische Muster
        for pattern in vague_patterns:
            if re.search(pattern, question_lower):
                return True
        
        # Prüfe auf sehr kurze oder generische Fragen
        if len(question.split()) <= 3:
            return True
            
        # Prüfe auf generische Wörter ohne Kontext
        generic_words = ["hilfe", "problem", "tun", "machen", "erfolg", "besser", "mehr", "weniger"]
        if any(word in question_lower for word in generic_words) and len(question.split()) <= 5:
            return True
            
        return False
    
    def is_question_specific_enough(self, question: str) -> bool:
        """Erkennt, ob eine Frage spezifisch genug ist für eine Antwort"""
        
        question_lower = question.lower().strip()
        
        # Spezifische Indikatoren
        specific_indicators = [
            "kg", "kilo", "woche", "tag", "stunde", "minute",  # Zeit/Gewicht
            "sport", "training", "laufen", "fitness", "gym",   # Sport
            "fleisch", "gemüse", "obst", "wasser", "kalorien", # Ernährung
            "leads", "kunden", "verkauf", "marketing", "social media", # Business
            "euro", "dollar", "budget", "kosten", "preis",     # Finanzen
            "team", "mitarbeiter", "angestellte", "freelancer", # Personal
            "website", "online", "shop", "app", "software"     # Technologie
        ]
        
        # Zähle spezifische Indikatoren
        specific_count = sum(1 for indicator in specific_indicators if indicator in question_lower)
        
        # Frage ist spezifisch genug wenn:
        # 1. Mindestens 2 spezifische Indikatoren vorhanden sind
        # 2. Oder die Frage länger als 10 Wörter ist
        # 3. Oder konkrete Zahlen enthalten sind
        has_numbers = bool(re.search(r'\d+', question))
        
        return (specific_count >= 2 or 
                len(question.split()) > 10 or 
                has_numbers)
    
    def generate_clarification_questions(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generiert spezifische Nachfragen basierend auf der ursprünglichen Frage und dem Kontext"""
        
        # Baue Kontext für die Nachfrage-Generierung
        context_text = self._build_context_for_clarification(context_chunks)
        
        clarification_prompt = f"""Du bist ein erfahrener Coach, der gezielt nachfragt, um spezifische Antworten zu geben.

Ursprüngliche Frage: "{question}"

Verfügbarer Kontext aus den Videos:
{context_text}

Deine Aufgabe: Erkenne, was in der ursprünglichen Frage zu unspezifisch ist und stelle 3-5 gezielte Nachfragen, die dem Fragesteller helfen, seine Frage zu präzisieren. Nutze dabei den verfügbaren Kontext, um relevante Nachfragen zu stellen.

Beispiele für gute Nachfragen:
- Bei "ich möchte abnehmen": "Wie viel möchtest du abnehmen? Wie viel Sport machst du aktuell? Wie ernährst du dich gerade? Welche Diäten hast du schon probiert?"
- Bei "ich möchte mehr Leads": "Für welches Produkt/Service möchtest du mehr Leads? In welchem Bereich arbeitest du? Was machst du bereits für Lead-Generierung?"

Stelle die Nachfragen in einem freundlichen, aber direkten Ton. Verwende "du" und sei konkret.
Antworte NUR mit den Nachfragen, keine zusätzlichen Erklärungen."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Verwende GPT-4o für bessere Nachfragen
                messages=[
                    {"role": "system", "content": "Du bist ein erfahrener Coach, der gezielt nachfragt."},
                    {"role": "user", "content": clarification_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            clarification = response.choices[0].message.content.strip()
            
            # Speichere in der Historie
            self.clarification_history.append({
                "original_question": question,
                "clarification": clarification,
                "timestamp": self._get_timestamp()
            })
            
            return clarification
            
        except Exception as e:
            logger.error(f"Clarification generation failed: {e}")
            return "Könntest du deine Frage etwas spezifischer stellen? Was genau möchtest du wissen?"
    
    def generate_answer_with_followup_questions(self, question: str, context_chunks: List[Dict[str, Any]], system_prompt: Optional[str] = None, conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generiert eine Antwort UND weitere Nachfragen für noch bessere Hilfe"""
        
        # Use more chunks for comprehensive answers (up to 30)
        max_chunks = min(30, len(context_chunks))
        selected_chunks = context_chunks[:max_chunks]
        
        # Baue Kontext für die Antwort
        context_text = self._build_context_for_clarification(selected_chunks)
        
        # Build conversation history context
        history_context = ""
        if conversation_history and len(conversation_history) > 0:
            history_parts = []
            for entry in conversation_history[-5:]:  # Last 5 conversations
                history_parts.append(f"Frage: {entry.get('question', '')}")
                history_parts.append(f"Antwort: {entry.get('answer', '')}")
            history_context = "\n\nVorherige Unterhaltung:\n" + "\n\n".join(history_parts)
        
        # Generiere Antwort mit dem bereitgestellten System-Prompt
        if system_prompt:
            answer_prompt = f"""Kontext aus dem Video:
{context_text}{history_context}

Frage: {question}

Antworte basierend auf dem bereitgestellten Kontext und der Unterhaltungshistorie. Gib eine umfassende, detaillierte Antwort. Wenn die Antwort nicht im Kontext gefunden werden kann, sage das ehrlich."""
        else:
            answer_prompt = f"""Du bist ein hilfreicher Assistent, der Fragen zu Video-Inhalten beantwortet.

Kontext aus dem Video:
{context_text}{history_context}

Frage: {question}

Antworte basierend auf dem bereitgestellten Kontext und der Unterhaltungshistorie. Gib eine umfassende, detaillierte Antwort. Verwende deutsche Sprache und sei präzise. Berücksichtige die vorherige Unterhaltung für einen natürlichen Gesprächsfluss."""

        try:
            # Generiere Antwort
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt or "Du bist ein hilfreicher Assistent für Video-Inhalte."},
                    {"role": "user", "content": answer_prompt}
                ],
                max_tokens=400,
                temperature=0.1
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Generiere weitere Nachfragen für noch bessere Hilfe
            followup_prompt = f"""Du bist ein erfahrener Coach. Du hast gerade eine Antwort gegeben, aber möchtest noch gezielter helfen.

Ursprüngliche Frage: "{question}"
Deine Antwort: "{answer}"

Verfügbarer Kontext aus den Videos:
{context_text}{history_context}

Deine Aufgabe: Stelle 2-3 zusätzliche Nachfragen, die dem Fragesteller helfen, sein Problem noch besser zu lösen. Diese sollten tiefer gehen als die ursprüngliche Frage und die Unterhaltung natürlich fortsetzen.

Berücksichtige die vorherige Unterhaltung, um:
- Nicht bereits besprochene Themen zu vermeiden
- Auf vorherige Antworten aufzubauen
- Die Unterhaltung logisch fortzusetzen

Beispiele:
- Bei Gewichtsabnahme: "Wie ist dein Schlafrhythmus? Trinkst du genug Wasser? Hast du Stress?"
- Bei Lead-Generierung: "Wie ist deine aktuelle Website? Nutzt du Social Media? Hast du ein Budget?"

Stelle die Nachfragen in einem freundlichen, aber direkten Ton. Verwende "du" und sei konkret.
Antworte NUR mit den Nachfragen, keine zusätzlichen Erklärungen."""

            followup_response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du bist ein erfahrener Coach, der gezielt nachfragt."},
                    {"role": "user", "content": followup_prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            followup_questions = followup_response.choices[0].message.content.strip()
            
            return {
                "answer": answer,
                "followup_questions": followup_questions,
                "context_chunks_used": len(selected_chunks),
                "total_chunks_found": len(context_chunks)
            }
            
        except Exception as e:
            logger.error(f"Answer with followup generation failed: {e}")
            return {
                "answer": "Entschuldigung, ich konnte keine Antwort generieren.",
                "followup_questions": "Könntest du deine Frage etwas spezifischer stellen?",
                "context_chunks_used": 0,
                "total_chunks_found": len(context_chunks)
            }
    
    def _build_context_for_clarification(self, chunks: List[Dict[str, Any]]) -> str:
        """Baut Kontext für die Nachfrage-Generierung"""
        
        if not chunks:
            return "Kein spezifischer Kontext verfügbar."
        
        # Use more chunks for better context (up to 15 for clarification)
        max_chunks = min(15, len(chunks))
        context_chunks = chunks[:max_chunks]
        
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            text = chunk.get('chunk_text', '')
            speaker = chunk.get('speaker', 'Unknown')
            
            context_parts.append(f"[{speaker}]: {text}")
        
        return "\n\n".join(context_parts)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_clarification_history(self) -> List[Dict[str, Any]]:
        """Gibt die Nachfrage-Historie zurück"""
        return self.clarification_history


class MiniChatAgent:
    """Mini chat agent for video content Q&A"""
    
    def __init__(self):
        """Initialize mini chat agent"""
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.video_processor = VideoProcessor()
        self.conversation_history = []
        
        # Initialize clarification mode
        self.clarification_mode = ClarificationMode(self.openai_client, self.video_processor)
        self.clarification_mode_enabled = True  # Automatisch aktiviert
        
        logger.info("Initialized MiniChatAgent with ClarificationMode")
    
    def ask_question(self, question: str, video_id: Optional[str] = None, 
                    context_limit: int = 20, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a question about video content with clarification mode
        
        Args:
            question: User's question
            video_id: Optional video ID to limit search
            context_limit: Number of relevant chunks to include
            system_prompt: Optional custom system prompt
            
        Returns:
            Response with answer and sources
        """
        logger.info(f"Processing question: '{question}'")
        
        try:
            # Search for relevant chunks first
            relevant_chunks = self.video_processor.search_video_content(
                question, video_id
            )
            
            # Check if clarification mode is enabled and question is too vague
            if (self.clarification_mode_enabled and 
                self.clarification_mode.is_question_too_vague(question)):
                
                logger.info("Question detected as vague, generating clarification questions")
                
                # Generate clarification questions
                clarification = self.clarification_mode.generate_clarification_questions(
                    question, relevant_chunks
                )
                
                # Calculate confidence based on found chunks
                confidence = self._calculate_confidence(relevant_chunks[:10], question)
                
                return {
                    "answer": f"🤔 Deine Frage ist noch etwas unspezifisch. Um dir die beste Antwort zu geben, brauche ich mehr Details:\n\n{clarification}\n\nBitte beantworte diese Fragen, dann kann ich dir eine gezielte Antwort geben!",
                    "sources": self._format_sources(relevant_chunks[:10]),  # Use more chunks for clarification
                    "confidence": confidence,
                    "context_chunks_used": 10,  # Use first 10 chunks for clarification
                    "total_chunks_found": len(relevant_chunks),
                    "clarification_mode": True,
                    "clarification_questions": clarification
                }
            
            # Check if question is specific enough for answer + followup questions
            elif (self.clarification_mode_enabled and 
                  self.clarification_mode.is_question_specific_enough(question) and
                  relevant_chunks):
                
                logger.info("Question is specific enough, generating answer with followup questions")
                
                # Generate answer with followup questions
                result = self.clarification_mode.generate_answer_with_followup_questions(
                    question, relevant_chunks, system_prompt, self.conversation_history
                )
                
                # Calculate confidence using more chunks
                confidence = self._calculate_confidence(relevant_chunks[:30], question)
                
                return {
                    "answer": f"{result['answer']}\n\n🤔 Um dir noch besser helfen zu können, habe ich noch ein paar weitere Fragen:\n\n{result['followup_questions']}\n\nBitte beantworte diese, dann kann ich dir noch gezielter helfen!",
                    "sources": self._format_sources(relevant_chunks[:30]),
                    "confidence": confidence,
                    "context_chunks_used": result['context_chunks_used'],
                    "total_chunks_found": result['total_chunks_found'],
                    "clarification_mode": True,
                    "followup_questions": result['followup_questions']
                }
            
            # If question is specific enough or clarification mode is disabled, proceed normally
            if not relevant_chunks:
                return {
                    "answer": "Entschuldigung, ich konnte keine relevanten Informationen zu Ihrer Frage finden.",
                    "sources": [],
                    "confidence": 0.0,
                    "context_chunks_used": 0,
                    "total_chunks_found": 0
                }
            
            # Limit context to avoid token limits
            context_chunks = relevant_chunks[:context_limit]
            
            # Build context for LLM
            context_text = self._build_context(context_chunks)
            
            # Generate answer using LLM
            answer = self._generate_answer(question, context_text, system_prompt)
            
            # Calculate confidence based on chunk relevance
            confidence = self._calculate_confidence(context_chunks, question)
            
            # Prepare response
            response = {
                "answer": answer,
                "sources": self._format_sources(context_chunks),
                "confidence": confidence,
                "context_chunks_used": len(context_chunks),
                "total_chunks_found": len(relevant_chunks),
                "clarification_mode": False
            }
            
            # Add to conversation history
            self.conversation_history.append({
                "question": question,
                "answer": answer,
                "timestamp": self._get_timestamp()
            })
            
            logger.info(f"Generated answer with confidence: {confidence:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to process question: {e}")
            return {
                "answer": f"Entschuldigung, es ist ein Fehler aufgetreten: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "context_chunks_used": 0,
                "total_chunks_found": 0
            }
    
    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Build context text from relevant chunks"""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('chunk_text', '')
            timestamp = chunk.get('start_timestamp', 0)
            speaker = chunk.get('speaker', 'Unknown')
            
            context_parts.append(
                f"[Chunk {i} - {timestamp:.1f}s - {speaker}]: {text}"
            )
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str, system_prompt: Optional[str] = None) -> str:
        """Generate answer using OpenAI LLM"""
        
        # Use custom system prompt if provided, otherwise use default
        if system_prompt:
            system_content = system_prompt
            user_prompt = f"""Kontext aus dem Video:
{context}

Frage: {question}

Antworte basierend auf dem bereitgestellten Kontext. Wenn die Antwort nicht im Kontext gefunden werden kann, sage das ehrlich."""
        else:
            system_content = "Du bist ein hilfreicher Assistent für Video-Inhalte."
            user_prompt = f"""Du bist ein hilfreicher Assistent, der Fragen zu Video-Inhalten beantwortet.

Kontext aus dem Video:
{context}

Frage: {question}

Antworte basierend auf dem bereitgestellten Kontext. Wenn die Antwort nicht im Kontext gefunden werden kann, sage das ehrlich. Verwende deutsche Sprache und sei präzise."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "Entschuldigung, ich konnte keine Antwort generieren."
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for response"""
        
        sources = []
        for chunk in chunks:
            source = {
                "text": chunk.get('chunk_text', '')[:200] + "...",
                "timestamp": chunk.get('start_timestamp', 0),
                "speaker": chunk.get('speaker', 'Unknown'),
                "video_id": chunk.get('video_id', 'Unknown')
            }
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, chunks: List[Dict[str, Any]], question: str) -> float:
        """Calculate confidence based on chunk relevance"""
        
        if not chunks:
            return 0.0
        
        # Simple confidence calculation based on number of chunks found
        # In a real implementation, you'd use semantic similarity scores
        base_confidence = min(len(chunks) / 3.0, 1.0)  # Max confidence with 3+ chunks
        
        # Adjust based on chunk quality (length, speaker info, etc.)
        quality_bonus = 0.0
        for chunk in chunks:
            if chunk.get('speaker'):
                quality_bonus += 0.1
            if len(chunk.get('chunk_text', '')) > 100:
                quality_bonus += 0.1
        
        final_confidence = min(base_confidence + quality_bonus, 1.0)
        return round(final_confidence, 2)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def toggle_clarification_mode(self, enabled: bool = None) -> bool:
        """Toggle clarification mode on/off"""
        if enabled is None:
            self.clarification_mode_enabled = not self.clarification_mode_enabled
        else:
            self.clarification_mode_enabled = enabled
        
        logger.info(f"Clarification mode {'enabled' if self.clarification_mode_enabled else 'disabled'}")
        return self.clarification_mode_enabled
    
    def get_clarification_history(self) -> List[Dict[str, Any]]:
        """Get clarification history"""
        return self.clarification_mode.get_clarification_history()
    
    def is_clarification_mode_enabled(self) -> bool:
        """Check if clarification mode is enabled"""
        return self.clarification_mode_enabled


class InteractiveChatSession:
    """Interactive chat session for testing"""
    
    def __init__(self, video_id: Optional[str] = None):
        """Initialize chat session"""
        self.agent = MiniChatAgent()
        self.video_id = video_id
        
        print("🤖 Mini Chat Agent initialized!")
        if video_id:
            print(f"📹 Focused on video: {video_id}")
        print("💡 Type 'quit' to exit, 'history' to see conversation, 'clear' to clear history")
        print("-" * 60)
    
    def start_session(self):
        """Start interactive chat session"""
        
        while True:
            try:
                question = input("\n❓ Your question: ").strip()
                
                if question.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                elif question.lower() == 'history':
                    self._show_history()
                    continue
                elif question.lower() == 'clear':
                    self.agent.clear_history()
                    print("🧹 History cleared!")
                    continue
                elif not question:
                    continue
                
                # Process question
                print("🔍 Searching for relevant content...")
                response = self.agent.ask_question(question, self.video_id)
                
                # Display response
                print(f"\n🤖 Answer:")
                print(f"   {response['answer']}")
                
                print(f"\n📊 Confidence: {response['confidence']}")
                
                # Handle the context_chunks_used field properly
                if 'context_chunks_used' in response:
                    print(f"📚 Sources used: {response['context_chunks_used']}/{response['total_chunks_found']}")
                else:
                    print(f"📚 Sources used: {len(response.get('sources', []))}/{response.get('total_chunks_found', 0)}")
                
                if response.get('sources'):
                    print(f"\n📝 Sources:")
                    for i, source in enumerate(response['sources'], 1):
                        print(f"   {i}. [{source['timestamp']:.1f}s] {source['speaker']}: {source['text']}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_history(self):
        """Show conversation history"""
        history = self.agent.get_conversation_history()
        
        if not history:
            print("📝 No conversation history yet.")
            return
        
        print(f"\n📝 Conversation History ({len(history)} exchanges):")
        print("-" * 40)
        
        for i, exchange in enumerate(history, 1):
            print(f"{i}. Q: {exchange['question']}")
            print(f"   A: {exchange['answer'][:100]}...")
            print(f"   Time: {exchange['timestamp']}")
            print()
