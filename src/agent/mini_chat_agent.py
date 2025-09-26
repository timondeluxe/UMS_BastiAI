"""
Mini Chat Agent for video content retrieval and Q&A
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from openai import OpenAI
from config.settings import settings
from src.embedding.embedding_generator import VideoProcessor


logger = logging.getLogger(__name__)


class MiniChatAgent:
    """Mini chat agent for video content Q&A"""
    
    def __init__(self):
        """Initialize mini chat agent"""
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.video_processor = VideoProcessor()
        self.conversation_history = []
        
        logger.info("Initialized MiniChatAgent")
    
    def ask_question(self, question: str, video_id: Optional[str] = None, 
                    context_limit: int = 20, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a question about video content
        
        Args:
            question: User's question
            video_id: Optional video ID to limit search
            context_limit: Number of relevant chunks to include
            
        Returns:
            Response with answer and sources
        """
        logger.info(f"Processing question: '{question}'")
        
        try:
            # Search for relevant chunks
            relevant_chunks = self.video_processor.search_video_content(
                question, video_id
            )
            
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
                "total_chunks_found": len(relevant_chunks)
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
