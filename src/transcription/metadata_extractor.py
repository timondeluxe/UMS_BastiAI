"""
Speaker identification and metadata extraction for transcriptions
"""

import logging
from typing import Dict, List, Optional, Any
import re
from collections import Counter

from pydantic import BaseModel, Field

from src.transcription.whisper_client import TranscriptionSegment


logger = logging.getLogger(__name__)


class SpeakerInfo(BaseModel):
    """Information about a speaker"""
    name: str = Field(description="Speaker name or identifier")
    segments_count: int = Field(description="Number of segments by this speaker")
    total_duration: float = Field(description="Total speaking time in seconds")
    word_count: int = Field(description="Total words spoken")
    avg_segment_length: float = Field(description="Average segment length in seconds")


class TranscriptionMetadata(BaseModel):
    """Enhanced metadata for transcription"""
    speakers: List[SpeakerInfo] = Field(description="Information about speakers")
    speaker_changes: int = Field(description="Number of speaker changes")
    avg_speaking_rate: float = Field(description="Average words per minute")
    silence_periods: List[Dict[str, float]] = Field(description="Periods of silence")
    quality_metrics: Dict[str, Any] = Field(description="Audio quality metrics")


class MetadataExtractor:
    """Extract metadata and speaker information from transcriptions"""
    
    def __init__(self):
        """Initialize metadata extractor"""
        self.speaker_patterns = [
            r"^(?:Bastian|Schmidt|Bastian Schmidt)",
            r"^(?:Moderator|Host|Presenter)",
            r"^(?:Speaker|Sprecher)\s*\d+",
            r"^(?:Person|User)\s*\d+"
        ]
        logger.info("Metadata extractor initialized")
    
    def extract_metadata(self, segments: List[TranscriptionSegment], 
                        video_duration: float) -> TranscriptionMetadata:
        """
        Extract comprehensive metadata from transcription segments
        
        Args:
            segments: List of transcription segments
            video_duration: Total video duration in seconds
            
        Returns:
            TranscriptionMetadata with speaker info and quality metrics
        """
        logger.info(f"Extracting metadata from {len(segments)} segments")
        
        # Extract speaker information
        speakers = self._identify_speakers(segments)
        
        # Calculate speaker changes
        speaker_changes = self._count_speaker_changes(segments)
        
        # Calculate speaking rate
        avg_speaking_rate = self._calculate_speaking_rate(segments)
        
        # Identify silence periods
        silence_periods = self._identify_silence_periods(segments, video_duration)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(segments)
        
        return TranscriptionMetadata(
            speakers=speakers,
            speaker_changes=speaker_changes,
            avg_speaking_rate=avg_speaking_rate,
            silence_periods=silence_periods,
            quality_metrics=quality_metrics
        )
    
    def _identify_speakers(self, segments: List[TranscriptionSegment]) -> List[SpeakerInfo]:
        """Identify speakers and calculate their statistics"""
        
        # Group segments by speaker
        speaker_segments = {}
        for segment in segments:
            speaker = segment.speaker or "Unknown"
            if speaker not in speaker_segments:
                speaker_segments[speaker] = []
            speaker_segments[speaker].append(segment)
        
        # Calculate speaker statistics
        speakers = []
        for speaker_name, segs in speaker_segments.items():
            total_duration = sum(seg.end - seg.start for seg in segs)
            word_count = sum(len(seg.text.split()) for seg in segs)
            avg_segment_length = total_duration / len(segs) if segs else 0
            
            speaker_info = SpeakerInfo(
                name=speaker_name,
                segments_count=len(segs),
                total_duration=total_duration,
                word_count=word_count,
                avg_segment_length=avg_segment_length
            )
            speakers.append(speaker_info)
        
        # Sort by total duration (most active speaker first)
        speakers.sort(key=lambda x: x.total_duration, reverse=True)
        
        return speakers
    
    def _count_speaker_changes(self, segments: List[TranscriptionSegment]) -> int:
        """Count the number of speaker changes"""
        if len(segments) < 2:
            return 0
        
        changes = 0
        prev_speaker = segments[0].speaker
        
        for segment in segments[1:]:
            current_speaker = segment.speaker
            if prev_speaker != current_speaker:
                changes += 1
            prev_speaker = current_speaker
        
        return changes
    
    def _calculate_speaking_rate(self, segments: List[TranscriptionSegment]) -> float:
        """Calculate average speaking rate (words per minute)"""
        if not segments:
            return 0.0
        
        total_words = sum(len(seg.text.split()) for seg in segments)
        total_duration = sum(seg.end - seg.start for seg in segments)
        
        if total_duration == 0:
            return 0.0
        
        # Convert to words per minute
        words_per_second = total_words / total_duration
        words_per_minute = words_per_second * 60
        
        return words_per_minute
    
    def _identify_silence_periods(self, segments: List[TranscriptionSegment], 
                                 video_duration: float, min_silence_duration: float = 2.0) -> List[Dict[str, float]]:
        """Identify periods of silence between segments"""
        
        silence_periods = []
        
        # Sort segments by start time
        sorted_segments = sorted(segments, key=lambda x: x.start)
        
        # Check for silence at the beginning
        if sorted_segments and sorted_segments[0].start > min_silence_duration:
            silence_periods.append({
                "start": 0.0,
                "end": sorted_segments[0].start,
                "duration": sorted_segments[0].start
            })
        
        # Check for silence between segments
        for i in range(len(sorted_segments) - 1):
            current_end = sorted_segments[i].end
            next_start = sorted_segments[i + 1].start
            
            if next_start - current_end > min_silence_duration:
                silence_periods.append({
                    "start": current_end,
                    "end": next_start,
                    "duration": next_start - current_end
                })
        
        # Check for silence at the end
        if sorted_segments and sorted_segments[-1].end < video_duration - min_silence_duration:
            silence_periods.append({
                "start": sorted_segments[-1].end,
                "end": video_duration,
                "duration": video_duration - sorted_segments[-1].end
            })
        
        return silence_periods
    
    def _calculate_quality_metrics(self, segments: List[TranscriptionSegment]) -> Dict[str, Any]:
        """Calculate quality metrics for the transcription"""
        
        if not segments:
            return {}
        
        # Confidence scores
        confidence_scores = [seg.confidence for seg in segments if seg.confidence is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
        
        # Text quality metrics
        word_counts = [len(seg.text.split()) for seg in segments]
        char_counts = [len(seg.text) for seg in segments]
        
        # Segment length distribution
        segment_lengths = [seg.end - seg.start for seg in segments]
        
        # Text complexity (average word length)
        all_words = " ".join(seg.text for seg in segments).split()
        avg_word_length = sum(len(word) for word in all_words) / len(all_words) if all_words else 0
        
        return {
            "avg_confidence": avg_confidence,
            "total_segments": len(segments),
            "avg_segment_length": sum(segment_lengths) / len(segment_lengths),
            "min_segment_length": min(segment_lengths),
            "max_segment_length": max(segment_lengths),
            "avg_words_per_segment": sum(word_counts) / len(word_counts),
            "avg_chars_per_segment": sum(char_counts) / len(char_counts),
            "avg_word_length": avg_word_length,
            "total_words": sum(word_counts),
            "total_characters": sum(char_counts)
        }
    
    def detect_speaker_names(self, text: str) -> List[str]:
        """Detect potential speaker names in text"""
        
        # Common German names and titles
        name_patterns = [
            r"\b(?:Herr|Frau|Dr\.|Prof\.)\s+[A-Z][a-z]+",
            r"\b[A-Z][a-z]+\s+[A-Z][a-z]+",  # First Last
            r"\b(?:Bastian|Schmidt|Max|Anna|Thomas|Maria|Peter|Lisa)\b"
        ]
        
        detected_names = set()
        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            detected_names.update(matches)
        
        return list(detected_names)
    
    def extract_keywords(self, segments: List[TranscriptionSegment], 
                       min_frequency: int = 3) -> List[Dict[str, Any]]:
        """Extract frequently mentioned keywords"""
        
        # Combine all text
        all_text = " ".join(seg.text for seg in segments).lower()
        
        # Simple keyword extraction (can be enhanced with NLP libraries)
        words = re.findall(r'\b[a-zA-ZäöüßÄÖÜ]{3,}\b', all_text)
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Filter by minimum frequency
        keywords = [
            {"word": word, "frequency": count, "percentage": count / len(words) * 100}
            for word, count in word_counts.items()
            if count >= min_frequency
        ]
        
        # Sort by frequency
        keywords.sort(key=lambda x: x["frequency"], reverse=True)
        
        return keywords[:20]  # Top 20 keywords
