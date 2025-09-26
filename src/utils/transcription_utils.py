"""
Utility functions for loading and managing transcriptions
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.transcription.whisper_client import TranscriptionSegment, TranscriptionResult


logger = logging.getLogger(__name__)


def load_transcription(video_id: str) -> Optional[Dict]:
    """
    Load a saved transcription from JSON file
    
    Args:
        video_id: Video ID to load
        
    Returns:
        Transcription data as dictionary or None if not found
    """
    transcription_file = Path("transcriptions") / f"{video_id}.json"
    
    if not transcription_file.exists():
        logger.warning(f"Transcription file not found: {transcription_file}")
        return None
    
    try:
        with open(transcription_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded transcription: {video_id}")
        return data
    except Exception as e:
        logger.error(f"Error loading transcription {video_id}: {e}")
        return None


def load_transcription_as_result(video_id: str) -> Optional[TranscriptionResult]:
    """
    Load a saved transcription and convert to TranscriptionResult object
    
    Args:
        video_id: Video ID to load
        
    Returns:
        TranscriptionResult object or None if not found
    """
    data = load_transcription(video_id)
    if not data:
        return None
    
    try:
        # Convert segments back to TranscriptionSegment objects
        segments = []
        for seg_data in data["segments"]:
            segment = TranscriptionSegment(
                start=seg_data["start"],
                end=seg_data["end"],
                text=seg_data["text"],
                speaker=seg_data.get("speaker"),
                confidence=seg_data.get("confidence")
            )
            segments.append(segment)
        
        # Create TranscriptionResult object
        result = TranscriptionResult(
            video_id=data["video_id"],
            text=" ".join([seg.text for seg in segments]),
            segments=segments,
            language=data["language"],
            duration=data["duration"],
            metadata=data["metadata"]
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error converting transcription data {video_id}: {e}")
        return None


def list_transcriptions() -> List[str]:
    """
    List all available transcription video IDs
    
    Returns:
        List of video IDs that have saved transcriptions
    """
    transcriptions_dir = Path("transcriptions")
    if not transcriptions_dir.exists():
        return []
    
    video_ids = []
    for file_path in transcriptions_dir.glob("*.json"):
        video_id = file_path.stem
        video_ids.append(video_id)
    
    return sorted(video_ids)


def get_transcription_info(video_id: str) -> Optional[Dict]:
    """
    Get basic info about a transcription without loading full data
    
    Args:
        video_id: Video ID to get info for
        
    Returns:
        Dictionary with basic info or None if not found
    """
    data = load_transcription(video_id)
    if not data:
        return None
    
    return {
        "video_id": data["video_id"],
        "filename": data["filename"],
        "duration": data["duration"],
        "language": data["language"],
        "segment_count": len(data["segments"]),
        "word_count": data["metadata"].get("word_count", 0),
        "character_count": data["metadata"].get("character_count", 0),
        "avg_speaking_rate": data["metadata"].get("avg_speaking_rate", 0),
        "speakers": len(data["metadata"].get("speakers", []))
    }


def transcription_exists(video_id: str) -> bool:
    """
    Check if a transcription exists for a video ID
    
    Args:
        video_id: Video ID to check
        
    Returns:
        True if transcription exists, False otherwise
    """
    transcription_file = Path("transcriptions") / f"{video_id}.json"
    return transcription_file.exists()
