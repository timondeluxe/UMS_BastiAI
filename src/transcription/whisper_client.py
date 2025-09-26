"""
OpenAI Whisper client for video transcription
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import subprocess

from openai import OpenAI
from pydantic import BaseModel, Field

from config.settings import settings


logger = logging.getLogger(__name__)


class TranscriptionSegment(BaseModel):
    """Model for transcription segments with timestamps"""
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    text: str = Field(description="Transcribed text")
    speaker: Optional[str] = Field(default=None, description="Speaker identification")
    confidence: Optional[float] = Field(default=None, description="Confidence score")


class TranscriptionResult(BaseModel):
    """Model for complete transcription result"""
    video_id: str = Field(description="Unique video identifier")
    text: str = Field(description="Full transcription text")
    segments: List[TranscriptionSegment] = Field(description="Segmented transcription")
    language: str = Field(description="Detected language")
    duration: float = Field(description="Total duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WhisperClient:
    """Client for OpenAI Whisper API transcription"""
    
    def __init__(self):
        """Initialize Whisper client"""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.transcription_whisper_model
        self.language = settings.transcription_language
        
        logger.info(f"Initialized Whisper client with model: {self.model}")
    
    def transcribe_video(self, video_path: Path) -> TranscriptionResult:
        """
        Transcribe a video file using OpenAI Whisper API
        
        Args:
            video_path: Path to the video file
            
        Returns:
            TranscriptionResult with full transcription and segments
        """
        logger.info(f"Starting transcription for: {video_path}")
        
        try:
            # Extract audio from video
            audio_path = self._extract_audio(video_path)
            logger.info(f"Audio extracted to: {audio_path}")
            
            # Check file size and split if necessary
            audio_files = self._prepare_audio_files(audio_path)
            
            # Transcribe each audio file
            all_segments = []
            full_text = ""
            
            for i, audio_file in enumerate(audio_files):
                logger.info(f"Transcribing audio file {i+1}/{len(audio_files)}")
                segments = self._transcribe_audio_file(audio_file, i)
                all_segments.extend(segments)
                full_text += " ".join([seg.text for seg in segments]) + " "
            
            # Clean up temporary files
            self._cleanup_temp_files(audio_path, audio_files)
            
            # Create result
            video_id = self._generate_video_id(video_path)
            result = TranscriptionResult(
                video_id=video_id,
                text=full_text.strip(),
                segments=all_segments,
                language=self.language,
                duration=self._get_video_duration(video_path),
                metadata=self._extract_metadata(video_path, all_segments)
            )
            
            logger.info(f"Transcription completed. Duration: {result.duration}s, Segments: {len(result.segments)}")
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing video {video_path}: {e}")
            raise
    
    def _extract_audio(self, video_path: Path) -> Path:
        """Extract audio from video file using ffmpeg"""
        temp_dir = Path(tempfile.gettempdir()) / "ums_chunking"
        temp_dir.mkdir(exist_ok=True)
        
        audio_path = temp_dir / f"{video_path.stem}_audio.wav"
        
        # Use ffmpeg to extract audio
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # Audio codec
            "-ar", str(settings.transcription_sample_rate),  # Sample rate
            "-ac", "1",  # Mono
            "-y",  # Overwrite
            str(audio_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"FFmpeg output: {result.stderr}")
            return audio_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install ffmpeg.")
    
    def _prepare_audio_files(self, audio_path: Path) -> List[Path]:
        """Prepare audio files for transcription (split if too large)"""
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        max_size_mb = 25  # OpenAI Whisper limit
        
        if file_size_mb <= max_size_mb:
            return [audio_path]
        
        logger.info(f"Audio file too large ({file_size_mb:.1f}MB), splitting...")
        return self._split_audio_file(audio_path)
    
    def _split_audio_file(self, audio_path: Path) -> List[Path]:
        """Split large audio file into smaller chunks"""
        temp_dir = audio_path.parent
        duration = self._get_audio_duration(audio_path)
        chunk_duration = 600  # 10 minutes per chunk
        
        audio_files = []
        chunk_count = int(duration / chunk_duration) + 1
        
        for i in range(chunk_count):
            start_time = i * chunk_duration
            chunk_path = temp_dir / f"{audio_path.stem}_chunk_{i}.wav"
            
            cmd = [
                "ffmpeg", "-i", str(audio_path),
                "-ss", str(start_time),
                "-t", str(chunk_duration),
                "-c", "copy",
                "-y",
                str(chunk_path)
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                audio_files.append(chunk_path)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to create chunk {i}: {e}")
        
        return audio_files
    
    def _transcribe_audio_file(self, audio_path: Path, chunk_index: int = 0) -> List[TranscriptionSegment]:
        """Transcribe a single audio file using OpenAI Whisper"""
        
        with open(audio_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=self.language,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        segments = []
        for segment in response.segments:
            # Adjust timestamps for chunked files
            start_time = segment.start + (chunk_index * 600)  # 10 minutes per chunk
            end_time = segment.end + (chunk_index * 600)
            
            transcription_segment = TranscriptionSegment(
                start=start_time,
                end=end_time,
                text=segment.text.strip(),
                confidence=getattr(segment, 'avg_logprob', None)
            )
            segments.append(transcription_segment)
        
        return segments
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe"""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(video_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            logger.warning(f"Could not determine duration for {video_path}")
            return 0.0
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration using ffprobe"""
        return self._get_video_duration(audio_path)  # Same command works for audio
    
    def _generate_video_id(self, video_path: Path) -> str:
        """
        Generate unique video ID from file content hash
        
        This ensures the same video gets the same ID even if:
        - Filename changes
        - File is moved to different location
        - File is processed multiple times
        """
        import hashlib
        
        try:
            # Generate hash from file content (first 1MB for efficiency)
            with open(video_path, 'rb') as f:
                # Read first 1MB of file
                content_sample = f.read(1024 * 1024)
            
            # Generate hash
            file_hash = hashlib.md5(content_sample).hexdigest()[:12]  # Use first 12 chars
            
            # Also include file size for additional uniqueness
            file_size = video_path.stat().st_size
            
            # Create video ID
            video_id = f"video_{file_hash}_{file_size}"
            
            logger.info(f"Generated video ID: {video_id} for {video_path.name}")
            return video_id
            
        except Exception as e:
            logger.warning(f"Could not generate content-based ID: {e}")
            # Fallback to filename-based ID
            clean_name = video_path.stem.replace(" ", "_").replace("-", "_")
            return f"video_{clean_name}"
    
    def _extract_metadata(self, video_path: Path, segments: List[TranscriptionSegment]) -> Dict[str, Any]:
        """Extract metadata from video and transcription"""
        word_count = sum(len(seg.text.split()) for seg in segments)
        char_count = sum(len(seg.text) for seg in segments)
        
        return {
            "filename": video_path.name,
            "file_size": video_path.stat().st_size,
            "word_count": word_count,
            "character_count": char_count,
            "segment_count": len(segments),
            "avg_segment_length": char_count / len(segments) if segments else 0,
            "transcription_model": self.model,
            "language": self.language
        }
    
    def _cleanup_temp_files(self, audio_path: Path, audio_files: List[Path]):
        """Clean up temporary audio files"""
        try:
            for file_path in audio_files:
                if file_path.exists() and file_path != audio_path:
                    file_path.unlink()
            if audio_path.exists():
                audio_path.unlink()
            logger.debug("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Failed to clean up temp files: {e}")
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            # Test with a small audio file or just check API key
            response = self.client.models.list()
            logger.info("OpenAI API connection successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI API connection failed: {e}")
            return False
