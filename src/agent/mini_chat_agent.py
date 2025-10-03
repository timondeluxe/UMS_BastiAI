"""
Mini Chat Agent for video content retrieval and Q&A
"""

import logging
import random
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
        self.iterative_mode = False  # One-question-at-a-time mode
        self.question_strategy = None  # Planned questions for iterative mode
        
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

Antworte basierend auf dem bereitgestellten Kontext und der Unterhaltungshistorie. Gib eine umfassende, detaillierte Antwort. Verwende verschiedene Einleitungen und einen direkten, motivierenden Ton wie "BOOM, lasst es uns direkt angehen!" oder ähnliche Variationen. Wenn die Antwort nicht im Kontext gefunden werden kann, sage das ehrlich."""
        else:
            answer_prompt = f"""Du bist ein hilfreicher Assistent, der Fragen zu Video-Inhalten beantwortet.

Kontext aus dem Video:
{context_text}{history_context}

Frage: {question}

Antworte basierend auf dem bereitgestellten Kontext und der Unterhaltungshistorie. Gib eine umfassende, detaillierte Antwort. Verwende deutsche Sprache und sei präzise. Verwende verschiedene motivierende Einleitungen wie "BOOM, lasst es uns direkt angehen!", "Perfekt, hier ist mein direkter Ansatz:", "Alles klar, lass uns das sofort anpacken:" oder ähnliche Variationen. Berücksichtige die vorherige Unterhaltung für einen natürlichen Gesprächsfluss."""

        try:
            # Generiere Antwort
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt or "Du bist ein hilfreicher Assistent für Video-Inhalte."},
                    {"role": "user", "content": answer_prompt}
                ],
                max_tokens=400,
                temperature=0.7  # Höhere Temperature für mehr Variationen
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

Stelle die Nachfragen in einem freundlichen, aber direkten Ton. Verwende "du" und sei konkret. Verwende verschiedene Formulierungen und Emojis für Abwechslung.
Antworte NUR mit den Nachfragen, keine zusätzlichen Erklärungen."""

            followup_response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du bist ein erfahrener Coach, der gezielt nachfragt."},
                    {"role": "user", "content": followup_prompt}
                ],
                max_tokens=200,
                temperature=0.8  # Höhere Temperature für mehr Variationen in Nachfragen
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
    
    def _get_random_answer_intro(self) -> str:
        """Gibt eine zufällige Einleitung für Antworten zurück"""
        intros = [
            "BOOM, lasst es uns direkt angehen!",
            "Perfekt, hier ist mein direkter Ansatz:",
            "Alles klar, lass uns das sofort anpacken:",
            "Genau das brauchst du - hier ist mein Plan:",
            "Super Frage! Lass mich dir das direkt erklären:",
            "Okay, hier ist mein ehrlicher Ansatz:",
            "Das ist ein wichtiges Thema - lass uns das richtig angehen:",
            "Verstehe! Hier ist mein direkter Ratschlag:",
            "Gute Frage! Lass mich dir das sofort zeigen:",
            "Hier ist mein ehrlicher Take dazu:",
            "Das ist genau das, was du brauchst:",
            "Lass uns das direkt und ehrlich angehen:",
            "Hier ist mein direkter Ansatz für dich:",
            "Perfekt! Lass mich dir das sofort erklären:",
            "Das ist ein wichtiger Punkt - hier ist mein Plan:"
        ]
        return random.choice(intros)
    
    def _get_random_followup_intro(self) -> str:
        """Gibt eine zufällige Einleitung für Nachfragen zurück"""
        intros = [
            "🤔 Um dir noch besser helfen zu können, habe ich noch ein paar weitere Fragen:",
            "💡 Lass mich noch ein paar wichtige Details wissen:",
            "🎯 Um dir gezielter helfen zu können, brauche ich noch:",
            "⚡ Für eine noch bessere Antwort, erzähl mir noch:",
            "🔥 Um das richtig zu lösen, brauche ich noch:",
            "💪 Für den perfekten Plan, sag mir noch:",
            "🚀 Um dir optimal zu helfen, erzähl mir:",
            "✨ Für eine maßgeschneiderte Lösung, brauche ich:",
            "🎪 Um das richtig anzugehen, sag mir noch:",
            "💎 Für die beste Strategie, erzähl mir:",
            "🔥 Um das richtig zu rocken, brauche ich noch:",
            "⚡ Für den perfekten Durchbruch, sag mir:",
            "🎯 Um dir gezielt zu helfen, erzähl mir noch:",
            "💪 Für den besten Ansatz, brauche ich:",
            "🚀 Um das richtig zu lösen, sag mir noch:"
        ]
        return random.choice(intros)
    
    def get_clarification_history(self) -> List[Dict[str, Any]]:
        """Gibt die Nachfrage-Historie zurück"""
        return self.clarification_history
    
    def create_question_strategy(self, initial_question: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Erstellt eine Fragen-Strategie am Anfang der iterativen Befragung.
        Definiert 5-7 wichtige Fragen, die beantwortet werden sollten.
        
        Returns:
            Dict mit 'questions' (List) und Metadaten
        """
        # Build context from chunks
        context_text = self._build_context_for_clarification(context_chunks[:10])
        
        strategy_prompt = f"""Du bist ein Experte für strukturierte Befragung. 

Ursprüngliche Frage: "{initial_question}"

Verfügbarer Kontext aus Videos:
{context_text[:1000]}

Deine Aufgabe: Erstelle eine Fragen-Strategie mit 5-7 wichtigen Fragen, die beantwortet werden sollten, um eine wirklich gute, maßgeschneiderte Antwort geben zu können.

Die Fragen sollten:
- Konkrete, messbare Details erfragen (Zahlen, Zeiträume, Budget, etc.)
- Verschiedene Aspekte abdecken (Situation, Ziel, Ressourcen, Herausforderungen, etc.)
- Aufeinander aufbauen
- Für den Nutzer leicht zu beantworten sein

Beispiele für gute Fragen-Strategien:

Bei "Ich möchte abnehmen":
1. Wie viel möchtest du abnehmen? (Ziel)
2. Wie viel Sport machst du aktuell pro Woche? (Status Quo)
3. Wie ernährst du dich derzeit? (Status Quo)
4. Bis wann möchtest du dein Ziel erreichen? (Zeitrahmen)
5. Was hast du bereits versucht? (Erfahrung)
6. Welche Hindernisse siehst du? (Herausforderungen)

Bei "Ich brauche mehr Leads":
1. Für welches Produkt/Service brauchst du Leads? (Kontext)
2. Wie viele Leads generierst du aktuell pro Monat? (Status Quo)
3. Was ist dein Budget für Marketing? (Ressourcen)
4. Welche Kanäle nutzt du bereits? (Status Quo)
5. Wer ist deine Zielgruppe? (Kontext)
6. Was ist dein Ziel an Leads pro Monat? (Ziel)

Antworte NUR mit einem JSON-Objekt in folgendem Format:
{{
  "questions": [
    {{"id": 1, "question": "Frage 1", "category": "Ziel/Status/Ressourcen/etc.", "answered": false}},
    {{"id": 2, "question": "Frage 2", "category": "...", "answered": false}},
    ...
  ],
  "total_questions": 5-7,
  "minimum_required": 3-4
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für strukturierte Befragung."},
                    {"role": "user", "content": strategy_prompt}
                ],
                max_tokens=500,
                temperature=0.4,
                response_format={"type": "json_object"}
            )
            
            strategy = json.loads(response.choices[0].message.content.strip())
            logger.info(f"Created question strategy with {len(strategy.get('questions', []))} questions")
            
            # Store strategy
            self.question_strategy = strategy
            
            return strategy
            
        except Exception as e:
            logger.error(f"Question strategy creation failed: {e}")
            # Fallback strategy
            return {
                "questions": [
                    {"id": 1, "question": "Kannst du mir mehr Details zu deiner aktuellen Situation geben?", "category": "Status Quo", "answered": False},
                    {"id": 2, "question": "Was ist dein konkretes Ziel?", "category": "Ziel", "answered": False},
                    {"id": 3, "question": "Welche Ressourcen (Zeit, Budget, etc.) hast du verfügbar?", "category": "Ressourcen", "answered": False}
                ],
                "total_questions": 3,
                "minimum_required": 2
            }
    
    def update_question_strategy_progress(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aktualisiert den Status der Fragen-Strategie basierend auf der Konversationshistorie.
        Markiert Fragen als beantwortet, wenn die Info in den Antworten vorhanden ist.
        
        Returns:
            Aktualisierte Strategie mit answered-Status
        """
        if not self.question_strategy:
            logger.warning("No question strategy to update")
            return None
        
        # Build conversation text with user answers
        conversation_text = []
        for entry in conversation_history:
            # Bot's question to user
            bot_question = entry.get('answer', '')  # The bot's clarification question
            conversation_text.append(f"Bot fragt: {bot_question}")
            
            # User's answer (if provided)
            user_answer = entry.get('user_answer', '')
            if user_answer:
                conversation_text.append(f"Nutzer antwortet: {user_answer}")
        
        conversation_context = "\n".join(conversation_text)
        
        # Ask GPT to analyze which questions have been answered
        questions_json = json.dumps(self.question_strategy['questions'], ensure_ascii=False)
        
        update_prompt = f"""Du bist ein Experte für Gesprächsanalyse.

Geplante Fragen-Strategie:
{questions_json}

Bisherige Unterhaltung:
{conversation_context}

Deine Aufgabe: Analysiere, welche der geplanten Fragen bereits beantwortet wurden (direkt oder indirekt) basierend auf der bisherigen Unterhaltung.

Eine Frage gilt als beantwortet, wenn:
- Die Information direkt genannt wurde
- Die Information implizit aus der Antwort hervorgeht
- Eine ähnliche Frage bereits beantwortet wurde

Antworte mit einem JSON-Objekt, das für jede Frage angibt, ob sie beantwortet wurde:
{{
  "questions": [
    {{"id": 1, "answered": true/false, "answer_found": "Kurze Zusammenfassung der Antwort wenn beantwortet, sonst null"}},
    {{"id": 2, "answered": true/false, "answer_found": "..."}},
    ...
  ]
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für Gesprächsanalyse."},
                    {"role": "user", "content": update_prompt}
                ],
                max_tokens=400,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            update_result = json.loads(response.choices[0].message.content.strip())
            
            # Update the strategy
            for i, question in enumerate(self.question_strategy['questions']):
                update_info = update_result['questions'][i]
                question['answered'] = update_info['answered']
                question['answer_found'] = update_info.get('answer_found')
            
            answered_count = sum(1 for q in self.question_strategy['questions'] if q['answered'])
            logger.info(f"Strategy update: {answered_count}/{len(self.question_strategy['questions'])} questions answered")
            
            return self.question_strategy
            
        except Exception as e:
            logger.error(f"Strategy update failed: {e}")
            return self.question_strategy
    
    def check_if_ready_for_final_answer(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analysiert die Konversationshistorie und entscheidet, ob genug Spezifität vorhanden ist
        für eine vollständige Antwort, oder ob noch eine Nachfrage nötig ist.
        
        Nutzt die Fragen-Strategie wenn vorhanden.
        
        Returns:
            Dict mit 'ready' (bool) und optional 'reason' (str)
        """
        if not conversation_history:
            return {"ready": False, "reason": "no_history"}
        
        # If we have a question strategy, use it
        if self.question_strategy:
            # Update strategy progress
            self.update_question_strategy_progress(conversation_history)
            
            # Count answered questions
            answered_count = sum(1 for q in self.question_strategy['questions'] if q.get('answered', False))
            total_questions = len(self.question_strategy['questions'])
            minimum_required = self.question_strategy.get('minimum_required', max(3, total_questions - 2))
            
            logger.info(f"Strategy check: {answered_count}/{total_questions} answered (minimum: {minimum_required})")
            
            # Check if minimum requirement is met
            if answered_count >= minimum_required:
                return {
                    "ready": True,
                    "confidence": answered_count / total_questions,
                    "reason": f"{answered_count} von {total_questions} Fragen beantwortet",
                    "answered_questions": answered_count,
                    "total_questions": total_questions
                }
            else:
                unanswered = [q for q in self.question_strategy['questions'] if not q.get('answered', False)]
                return {
                    "ready": False,
                    "confidence": answered_count / total_questions,
                    "reason": f"Noch {len(unanswered)} Fragen offen",
                    "missing_info": f"Noch {len(unanswered)} von {total_questions} Fragen offen",
                    "unanswered_questions": unanswered
                }
        
        # Fallback: Original logic without strategy
        # Build conversation context
        conversation_text = []
        for entry in conversation_history:
            bot_question = entry.get('answer', '')
            conversation_text.append(f"Bot fragt: {bot_question}")
            
            user_answer = entry.get('user_answer', '')
            if user_answer:
                conversation_text.append(f"Nutzer antwortet: {user_answer}")
        
        conversation_context = "\n".join(conversation_text)
        
        # Ask GPT-4o to analyze if we have enough information
        analysis_prompt = f"""Du bist ein Experte darin zu entscheiden, ob eine Unterhaltung genug Spezifität erreicht hat, um eine vollständige, hilfreiche Antwort zu geben.

Analysiere die folgende Unterhaltung:

{conversation_context}

Deine Aufgabe: Entscheide, ob wir jetzt genug spezifische Informationen haben, um eine wirklich gute, umfassende Antwort zu geben, oder ob wir noch mehr Details brauchen.

Eine Antwort ist bereit, wenn:
- Konkrete, messbare Details vorhanden sind (Zahlen, Zeiträume, etc.)
- Der Kontext klar ist (Situation, Ziel, Rahmenbedingungen)
- Mindestens 2-3 spezifische Aspekte genannt wurden
- Die Frage so konkret ist, dass man eine maßgeschneiderte Lösung geben kann

Eine Antwort ist NICHT bereit, wenn:
- Nur vage Aussagen gemacht wurden
- Wichtige Details fehlen (Budget, Zeitrahmen, aktuelle Situation, etc.)
- Weniger als 2-3 Nachfragen beantwortet wurden
- Die Antworten sehr kurz oder unspezifisch sind

Antworte NUR mit einem JSON-Objekt in folgendem Format:
{{
  "ready": true/false,
  "confidence": 0.0-1.0,
  "missing_info": "Was fehlt noch?" (nur wenn ready=false),
  "reason": "Kurze Begründung"
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für Gesprächsanalyse."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=200,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            logger.info(f"Readiness check: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            # Default: not ready after less than 3 exchanges
            return {
                "ready": len(conversation_history) >= 3,
                "confidence": 0.5,
                "reason": "Default check based on conversation length"
            }
    
    def generate_single_clarification_question(self, question: str, conversation_history: List[Dict[str, Any]], context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generiert EINE gezielte Nachfrage basierend auf der bisherigen Unterhaltung.
        Nutzt die Fragen-Strategie wenn vorhanden, um die nächste unbeantwortete Frage zu stellen.
        """
        # If we have a strategy, pick the next unanswered question
        if self.question_strategy:
            # Update strategy progress first
            self.update_question_strategy_progress(conversation_history)
            
            # Find first unanswered question
            unanswered_questions = [q for q in self.question_strategy['questions'] if not q.get('answered', False)]
            
            if unanswered_questions:
                next_question = unanswered_questions[0]
                logger.info(f"Using next question from strategy: {next_question['question']}")
                return next_question['question']
            else:
                # All questions answered, but not ready yet - ask for additional info
                logger.info("All strategy questions answered, asking for additional info")
                return "Gibt es noch etwas Wichtiges, das ich wissen sollte, um dir optimal zu helfen?"
        
        # Fallback: Generate question without strategy
        # Build conversation context
        conversation_text = []
        for entry in conversation_history:
            bot_question = entry.get('answer', '')
            conversation_text.append(f"Bot fragt: {bot_question}")
            
            user_answer = entry.get('user_answer', '')
            if user_answer:
                conversation_text.append(f"Nutzer antwortet: {user_answer}")
        
        conversation_context = "\n".join(conversation_text) if conversation_text else "Keine vorherige Unterhaltung"
        
        # Build context from chunks
        context_text = self._build_context_for_clarification(context_chunks)
        
        clarification_prompt = f"""Du bist ein erfahrener Coach, der durch gezielte Einzelfragen mehr Details erfährt.

Bisherige Unterhaltung:
{conversation_context}

Aktuelle Frage: "{question}"

Verfügbarer Kontext aus Videos:
{context_text[:1000]}

Deine Aufgabe: Stelle EINE gezielte, konkrete Nachfrage, um mehr spezifische Details zu erfahren. 

Die Nachfrage sollte:
- Auf das bisher Gesagte aufbauen
- Nach konkreten, messbaren Details fragen (Zahlen, Zeiträume, Budget, etc.)
- Kurz und präzise sein
- Dem Nutzer helfen, sein Problem besser zu formulieren
- NICHT bereits gestellte Fragen wiederholen

Beispiele für gute Nachfragen:
- "Wie viel Budget hast du dafür zur Verfügung?"
- "Wie viele Stunden pro Woche kannst du dafür investieren?"
- "Was hast du bisher schon versucht?"
- "Bis wann möchtest du dieses Ziel erreichen?"

Verwende einen freundlichen, direkten Ton mit "du". 
Antworte NUR mit der Nachfrage, keine Erklärungen."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Du bist ein erfahrener Coach."},
                    {"role": "user", "content": clarification_prompt}
                ],
                max_tokens=150,
                temperature=0.4
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Single clarification generation failed: {e}")
            return "Kannst du mir mehr Details dazu geben?"


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
        self.iterative_clarification_mode = False  # One-question-at-a-time mode
        
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
            
            # ===== ITERATIVE CLARIFICATION MODE =====
            if self.iterative_clarification_mode and relevant_chunks:
                logger.info("Iterative clarification mode active")
                
                # Create question strategy if this is the first question
                if not self.clarification_mode.question_strategy and len(self.conversation_history) == 0:
                    logger.info("Creating question strategy for iterative mode")
                    self.clarification_mode.create_question_strategy(question, relevant_chunks)
                else:
                    # This is a follow-up answer from the user
                    # Add the user's answer to the last bot question in history
                    if self.conversation_history:
                        last_entry = self.conversation_history[-1]
                        # Store user's answer as a follow-up
                        last_entry['user_answer'] = question
                        logger.info(f"User answer added to history: {question[:50]}...")
                
                # Check if we have enough specificity for a final answer
                readiness_check = self.clarification_mode.check_if_ready_for_final_answer(
                    self.conversation_history
                )
                
                if readiness_check.get('ready', False):
                    # We have enough information - generate comprehensive answer
                    logger.info("Ready for final answer - generating comprehensive response")
                    
                    # Use up to 30 chunks for comprehensive answer
                    context_chunks = relevant_chunks[:30]
                    context_text = self._build_context(context_chunks)
                    
                    # Build full conversation context with user answers
                    conversation_text = []
                    for entry in self.conversation_history:
                        bot_question = entry.get('answer', '')
                        conversation_text.append(f"Bot fragt: {bot_question}")
                        
                        user_answer = entry.get('user_answer', '')
                        if user_answer:
                            conversation_text.append(f"Nutzer antwortet: {user_answer}")
                    conversation_context = "\n\n".join(conversation_text)
                    
                    # Generate comprehensive answer
                    final_prompt = f"""Basierend auf der gesamten Unterhaltung, gib jetzt eine umfassende, detaillierte und hilfreiche Antwort.

Bisherige Unterhaltung:
{conversation_context}

Aktuelle Frage: {question}

Verfügbare Informationen aus Videos:
{context_text}

Gib eine vollständige, maßgeschneiderte Antwort basierend auf allen gesammelten Informationen. Sei spezifisch, konkret und hilfreich."""

                    if system_prompt:
                        system_content = system_prompt
                    else:
                        system_content = "Du bist ein hilfreicher Experte, der umfassende, maßgeschneiderte Lösungen gibt."
                    
                    response_obj = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_content},
                            {"role": "user", "content": final_prompt}
                        ],
                        max_tokens=600,
                        temperature=0.7
                    )
                    
                    final_answer = response_obj.choices[0].message.content.strip()
                    confidence = self._calculate_confidence(context_chunks, question)
                    
                    # Add to history
                    self.conversation_history.append({
                        "question": question,
                        "answer": final_answer,
                        "timestamp": self._get_timestamp()
                    })
                    
                    return {
                        "answer": final_answer,
                        "sources": self._format_sources(context_chunks),
                        "all_selected_chunks": self._format_sources(relevant_chunks),
                        "used_chunk_indices": list(range(len(context_chunks))),
                        "confidence": confidence,
                        "context_chunks_used": len(context_chunks),
                        "total_chunks_found": len(relevant_chunks),
                        "clarification_mode": True,
                        "iterative_mode": True,
                        "final_answer": True
                    }
                    
                else:
                    # Not ready yet - ask ONE clarification question
                    logger.info(f"Not ready for final answer: {readiness_check.get('reason', 'unknown')}")
                    
                    single_question = self.clarification_mode.generate_single_clarification_question(
                        question, self.conversation_history, relevant_chunks
                    )
                    
                    confidence = self._calculate_confidence(relevant_chunks[:10], question)
                    
                    # Random intro for single question
                    intros = [
                        "🤔 Interessant! Lass mich noch eine Sache wissen:",
                        "💡 Um dir besser zu helfen, beantworte mir noch:",
                        "🎯 Perfekt, eine Frage noch:",
                        "⚡ Fast da! Noch eine wichtige Info:",
                        "🔥 Super, sag mir noch:",
                        "💪 Okay! Eine Sache noch:",
                        "🚀 Verstehe! Lass mich noch wissen:"
                    ]
                    intro = random.choice(intros)
                    
                    answer = f"{intro}\n\n{single_question}"
                    
                    # Add to history
                    if len(self.conversation_history) == 0:
                        # First question - add initial entry with user's initial question
                        self.conversation_history.append({
                            "question": question,  # Initial user question (e.g., "Ich möchte abnehmen")
                            "answer": answer,  # Bot's first clarification question
                            "timestamp": self._get_timestamp()
                        })
                        logger.info("Added first entry to conversation history")
                    else:
                        # Not the first - add new entry for the next clarification question
                        # (user's answer was already added above as 'user_answer' to the previous entry)
                        self.conversation_history.append({
                            "question": None,  # No new initial question
                            "answer": answer,  # Bot's next clarification question
                            "timestamp": self._get_timestamp()
                        })
                        logger.info(f"Added follow-up entry to conversation history (total: {len(self.conversation_history)})")
                    
                    return {
                        "answer": answer,
                        "sources": self._format_sources(relevant_chunks[:10]),
                        "all_selected_chunks": self._format_sources(relevant_chunks),
                        "used_chunk_indices": list(range(min(10, len(relevant_chunks)))),
                        "confidence": confidence,
                        "context_chunks_used": 10,
                        "total_chunks_found": len(relevant_chunks),
                        "clarification_mode": True,
                        "iterative_mode": True,
                        "final_answer": False
                    }
            
            # ===== ORIGINAL CLARIFICATION MODE =====
            # Check if clarification mode is enabled
            if self.clarification_mode_enabled and relevant_chunks and not self.iterative_clarification_mode:
                
                # Check if this is a very vague question (first time asking) AND no conversation history
                if (self.clarification_mode.is_question_too_vague(question) and 
                    len(self.conversation_history) == 0):
                    logger.info("Question detected as very vague with no history, generating initial clarification questions")
                    
                    # Generate initial clarification questions
                    clarification = self.clarification_mode.generate_clarification_questions(
                        question, relevant_chunks
                    )
                    
                    # Calculate confidence based on found chunks
                    confidence = self._calculate_confidence(relevant_chunks[:10], question)
                    
                    # Zufällige Einleitung für Nachfragen
                    intro_variations = [
                        "🤔 Deine Frage ist noch etwas unspezifisch. Um dir die beste Antwort zu geben, brauche ich mehr Details:",
                        "💡 Lass mich das besser verstehen. Für eine gezielte Antwort brauche ich noch:",
                        "🎯 Um dir optimal helfen zu können, erzähl mir noch:",
                        "⚡ Für die beste Lösung brauche ich noch ein paar Details:",
                        "🔥 Um das richtig anzugehen, sag mir noch:",
                        "💪 Für den perfekten Plan brauche ich:",
                        "🚀 Um dir gezielt zu helfen, erzähl mir:",
                        "✨ Für eine maßgeschneiderte Antwort, sag mir:"
                    ]
                    intro = random.choice(intro_variations)
                    
                    return {
                        "answer": f"{intro}\n\n{clarification}\n\nBitte beantworte diese Fragen, dann kann ich dir eine gezielte Antwort geben!",
                        "sources": self._format_sources(relevant_chunks[:10]),
                        "all_selected_chunks": self._format_sources(relevant_chunks),
                        "used_chunk_indices": list(range(min(10, len(relevant_chunks)))),
                        "confidence": confidence,
                        "context_chunks_used": 10,
                        "total_chunks_found": len(relevant_chunks),
                        "clarification_mode": True,
                        "clarification_questions": clarification
                    }
                
                # For all other questions in clarification mode (including follow-up answers), provide answer + followup questions
                else:
                    logger.info("Generating answer with followup questions for clarification mode")
                    
                    # Generate answer with followup questions
                    result = self.clarification_mode.generate_answer_with_followup_questions(
                        question, relevant_chunks, system_prompt, self.conversation_history
                    )
                    
                    # Calculate confidence using more chunks
                    confidence = self._calculate_confidence(relevant_chunks[:30], question)
                    
                    # Add to conversation history
                    self.conversation_history.append({
                        "question": question,
                        "answer": result['answer'],
                        "timestamp": self._get_timestamp()
                    })
                    
                    # Zufällige Einleitung für Nachfragen
                    followup_intro = self.clarification_mode._get_random_followup_intro()
                    
                    return {
                        "answer": f"{result['answer']}\n\n{followup_intro}\n\n{result['followup_questions']}\n\nBitte beantworte diese, dann kann ich dir noch gezielter helfen!",
                        "sources": self._format_sources(relevant_chunks[:30]),
                        "all_selected_chunks": self._format_sources(relevant_chunks),
                        "used_chunk_indices": list(range(min(30, len(relevant_chunks)))),
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
                    "all_selected_chunks": [],
                    "used_chunk_indices": [],
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
                "all_selected_chunks": self._format_sources(relevant_chunks),  # All chunks found
                "used_chunk_indices": list(range(len(context_chunks))),  # Indices of chunks actually used
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
                "all_selected_chunks": [],
                "used_chunk_indices": [],
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
                "text": chunk.get('chunk_text', ''),  # Return full text, not truncated
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
        """Clear conversation history and question strategy"""
        self.conversation_history = []
        if hasattr(self, 'clarification_mode'):
            self.clarification_mode.question_strategy = None
        logger.info("Conversation history and question strategy cleared")
    
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
    
    def toggle_iterative_clarification_mode(self, enabled: bool = None) -> bool:
        """Toggle iterative clarification mode on/off"""
        if enabled is None:
            self.iterative_clarification_mode = not self.iterative_clarification_mode
        else:
            self.iterative_clarification_mode = enabled
        
        logger.info(f"Iterative clarification mode {'enabled' if self.iterative_clarification_mode else 'disabled'}")
        return self.iterative_clarification_mode
    
    def is_iterative_clarification_mode_enabled(self) -> bool:
        """Check if iterative clarification mode is enabled"""
        return self.iterative_clarification_mode


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
