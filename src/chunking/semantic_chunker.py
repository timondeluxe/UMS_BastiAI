"""
Semantic chunking implementation based on Chroma Research
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import re
from dataclasses import dataclass

from src.transcription.whisper_client import TranscriptionSegment
from config.settings import settings
from config.chunking_config import get_chunking_strategy, CHUNKING_STRATEGIES


logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    text: str
    start_timestamp: float
    end_timestamp: float
    chunk_index: int
    video_id: str
    word_count: int = 0
    character_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        self.word_count = len(self.text.split())
        self.character_count = len(self.text)


class SemanticChunker:
    """Semantic chunking based on Chroma Research findings"""
    
    def __init__(self, strategy: str = "semantic"):
        """Initialize semantic chunker"""
        self.strategy_config = get_chunking_strategy(strategy)
        self.max_chunk_size = self.strategy_config.max_chunk_size
        self.min_chunk_size = self.strategy_config.min_chunk_size
        self.overlap = self.strategy_config.overlap
        self.semantic_threshold = self.strategy_config.semantic_threshold
        
        logger.info(f"Initialized SemanticChunker with strategy: {strategy}")
        logger.info(f"Max chunk size: {self.max_chunk_size}, Overlap: {self.overlap}")
    
    def chunk_transcription(self, segments: List[TranscriptionSegment], 
                          video_id: str) -> List[Chunk]:
        """
        Chunk transcription segments using semantic strategy
        
        Args:
            segments: List of transcription segments
            video_id: Video identifier
            
        Returns:
            List of semantic chunks
        """
        logger.info(f"Chunking {len(segments)} segments for video {video_id}")
        
        # Combine segments into continuous text
        combined_text = self._combine_segments(segments)
        
        # Apply semantic chunking strategy
        if self.strategy_config.name == "semantic":
            chunks = self._semantic_chunking(combined_text, segments, video_id)
        elif self.strategy_config.name == "recursive":
            chunks = self._recursive_chunking(combined_text, segments, video_id)
        elif self.strategy_config.name == "video_optimized":
            chunks = self._video_optimized_chunking(combined_text, segments, video_id)
        else:
            chunks = self._fixed_chunking(combined_text, segments, video_id)
        
        logger.info(f"Created {len(chunks)} chunks from {len(segments)} segments")
        return chunks
    
    def _combine_segments(self, segments: List[TranscriptionSegment]) -> str:
        """Combine segments into continuous text"""
        text_parts = []
        for segment in segments:
            # Clean text and add space
            clean_text = segment.text.strip()
            if clean_text:
                text_parts.append(clean_text)
        
        return " ".join(text_parts)
    
    def _semantic_chunking(self, text: str, segments: List[TranscriptionSegment], 
                          video_id: str) -> List[Chunk]:
        """Semantic chunking based on sentence boundaries and content similarity"""
        
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # Check if adding this sentence would exceed max size
            if current_length + sentence_length > self.max_chunk_size and current_chunk:
                # Create chunk from current content
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_chunk_from_text(
                        chunk_text, segments, video_id, chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk with overlap
                if self.overlap > 0:
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_length = len(overlap_text)
                else:
                    current_chunk = []
                    current_length = 0
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunk = self._create_chunk_from_text(
                    chunk_text, segments, video_id, chunk_index
                )
                chunks.append(chunk)
        
        return chunks
    
    def _recursive_chunking(self, text: str, segments: List[TranscriptionSegment], 
                           video_id: str) -> List[Chunk]:
        """Recursive character splitting (baseline method)"""
        
        chunks = []
        chunk_index = 0
        
        # Simple character-based splitting
        for i in range(0, len(text), self.max_chunk_size - self.overlap):
            chunk_text = text[i:i + self.max_chunk_size]
            
            if len(chunk_text) >= self.min_chunk_size:
                chunk = self._create_chunk_from_text(
                    chunk_text, segments, video_id, chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    def _video_optimized_chunking(self, text: str, segments: List[TranscriptionSegment], 
                                 video_id: str) -> List[Chunk]:
        """Video-optimized chunking considering speaker changes"""
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        current_speaker = None
        
        for segment in segments:
            segment_text = segment.text.strip()
            if not segment_text:
                continue
            
            # Check for speaker change
            if current_speaker != segment.speaker and current_chunk:
                # Speaker changed, create chunk
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_chunk_from_text(
                        chunk_text, segments, video_id, chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Start new chunk
                current_chunk = []
                current_length = 0
            
            # Check size limit
            if current_length + len(segment_text) > self.max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_chunk_from_text(
                        chunk_text, segments, video_id, chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                current_chunk = []
                current_length = 0
            
            current_chunk.append(segment_text)
            current_length += len(segment_text)
            current_speaker = segment.speaker
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunk = self._create_chunk_from_text(
                    chunk_text, segments, video_id, chunk_index
                )
                chunks.append(chunk)
        
        return chunks
    
    def _fixed_chunking(self, text: str, segments: List[TranscriptionSegment], 
                       video_id: str) -> List[Chunk]:
        """Fixed-size chunking"""
        
        chunks = []
        chunk_index = 0
        
        for i in range(0, len(text), self.max_chunk_size):
            chunk_text = text[i:i + self.max_chunk_size]
            
            chunk = self._create_chunk_from_text(
                chunk_text, segments, video_id, chunk_index
            )
            chunks.append(chunk)
            chunk_index += 1
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting based on punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, chunk: List[str]) -> str:
        """Get overlap text from the end of current chunk"""
        if not chunk:
            return ""
        
        overlap_text = ""
        for sentence in reversed(chunk):
            if len(overlap_text) + len(sentence) <= self.overlap:
                overlap_text = sentence + " " + overlap_text
            else:
                break
        
        return overlap_text.strip()
    
    def _create_chunk_from_text(self, text: str, segments: List[TranscriptionSegment], 
                               video_id: str, chunk_index: int) -> Chunk:
        """Create a Chunk object from text and find corresponding timestamps"""
        
        # Find timestamps for this chunk
        start_time, end_time = self._find_timestamps_for_text(text, segments, chunk_index)
        
        return Chunk(
            text=text,
            start_timestamp=start_time,
            end_timestamp=end_time,
            chunk_index=chunk_index,
            video_id=video_id,
            metadata={
                "chunking_strategy": self.strategy_config.name,
                "max_chunk_size": self.max_chunk_size,
                "overlap": self.overlap
            }
        )
    
    def _find_timestamps_for_text(self, text: str, segments: List[TranscriptionSegment], chunk_index: int = 0) -> tuple:
        """Find start and end timestamps for a chunk of text using simple proportional approach"""
        
        # SIMPLE PROPORTIONAL APPROACH: Calculate timestamps based on chunk index
        video_start = segments[0].start
        video_end = segments[-1].end
        video_duration = video_end - video_start
        
        # Estimate total number of chunks (approximate)
        total_text_length = sum(len(seg.text) for seg in segments)
        avg_chunk_size = 400  # Target chunk size
        estimated_total_chunks = total_text_length / avg_chunk_size
        
        # Calculate position based on chunk index
        if chunk_index < estimated_total_chunks:
            position_ratio = chunk_index / estimated_total_chunks
        else:
            position_ratio = 0.95  # Near end of video
        
        # Calculate chunk duration based on text length
        chunk_length = len(text)
        chunk_duration_ratio = chunk_length / total_text_length
        chunk_duration = chunk_duration_ratio * video_duration
        
        # Ensure reasonable chunk duration (between 10 seconds and 2 minutes)
        chunk_duration = max(10.0, min(chunk_duration, 120.0))
        
        # Calculate timestamps
        start_time = video_start + (position_ratio * video_duration)
        end_time = start_time + chunk_duration
        
        # CRITICAL FIX: Prevent non-first chunks from getting start_timestamp = 0
        if chunk_index > 0 and start_time == 0:
            logger.warning(f"Chunk {chunk_index} would get start_timestamp=0, applying minimum offset")
            start_time = 0.1  # Minimum offset for non-first chunks
        
        # Ensure end_time doesn't exceed video duration
        if end_time > video_end:
            end_time = video_end
        
        # Ensure start_time doesn't exceed video duration
        if start_time > video_end:
            start_time = video_end - chunk_duration
        
        logger.debug(f"Chunk {chunk_index}: position_ratio={position_ratio:.3f}, "
                    f"duration={chunk_duration:.1f}s, timestamps={start_time:.1f}s-{end_time:.1f}s")
        
        return start_time, end_time
    
    def get_chunk_statistics(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """Get statistics about the created chunks"""
        
        if not chunks:
            return {}
        
        chunk_sizes = [len(chunk.text) for chunk in chunks]
        word_counts = [chunk.word_count for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": np.mean(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "avg_word_count": np.mean(word_counts),
            "total_words": sum(word_counts),
            "total_characters": sum(chunk_sizes),
            "strategy": self.strategy_config.name
        }
