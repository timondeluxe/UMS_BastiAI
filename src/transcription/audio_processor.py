"""
Audio processing utilities for video transcription
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple
import subprocess
import tempfile

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class AudioInfo(BaseModel):
    """Audio file information"""
    duration: float
    sample_rate: int
    channels: int
    bitrate: int
    format: str
    file_size: int


class AudioProcessor:
    """Utility class for audio processing operations"""
    
    def __init__(self):
        """Initialize audio processor"""
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.mp3', '.wav', '.m4a']
        logger.info("Audio processor initialized")
    
    def is_supported_format(self, file_path: Path) -> bool:
        """Check if file format is supported"""
        return file_path.suffix.lower() in self.supported_formats
    
    def get_audio_info(self, file_path: Path) -> AudioInfo:
        """Get detailed audio information using ffprobe"""
        
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            data = json.loads(result.stdout)
            
            # Find audio stream
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise ValueError("No audio stream found")
            
            format_info = data.get('format', {})
            
            return AudioInfo(
                duration=float(format_info.get('duration', 0)),
                sample_rate=int(audio_stream.get('sample_rate', 0)),
                channels=int(audio_stream.get('channels', 0)),
                bitrate=int(format_info.get('bit_rate', 0)),
                format=format_info.get('format_name', 'unknown'),
                file_size=int(format_info.get('size', 0))
            )
            
        except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to get audio info for {file_path}: {e}")
            raise
    
    def convert_to_wav(self, input_path: Path, output_path: Optional[Path] = None, 
                      sample_rate: int = 16000, channels: int = 1) -> Path:
        """Convert audio/video to WAV format"""
        
        if output_path is None:
            temp_dir = Path(tempfile.gettempdir()) / "ums_chunking"
            temp_dir.mkdir(exist_ok=True)
            output_path = temp_dir / f"{input_path.stem}_converted.wav"
        
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # Audio codec
            "-ar", str(sample_rate),  # Sample rate
            "-ac", str(channels),  # Channels
            "-y",  # Overwrite
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"Audio conversion completed: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio conversion failed: {e.stderr}")
            raise RuntimeError(f"Failed to convert audio: {e.stderr}")
    
    def split_audio(self, input_path: Path, chunk_duration: int = 600, 
                   overlap: int = 10) -> List[Path]:
        """Split audio file into chunks with overlap"""
        
        audio_info = self.get_audio_info(input_path)
        total_duration = audio_info.duration
        
        if total_duration <= chunk_duration:
            return [input_path]
        
        temp_dir = Path(tempfile.gettempdir()) / "ums_chunking"
        temp_dir.mkdir(exist_ok=True)
        
        chunks = []
        chunk_count = int(total_duration / (chunk_duration - overlap)) + 1
        
        for i in range(chunk_count):
            start_time = i * (chunk_duration - overlap)
            chunk_path = temp_dir / f"{input_path.stem}_chunk_{i:03d}.wav"
            
            cmd = [
                "ffmpeg", "-i", str(input_path),
                "-ss", str(start_time),
                "-t", str(chunk_duration),
                "-c", "copy",
                "-y",
                str(chunk_path)
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                chunks.append(chunk_path)
                logger.debug(f"Created chunk {i+1}/{chunk_count}: {chunk_path}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to create chunk {i}: {e}")
        
        return chunks
    
    def normalize_audio(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Normalize audio levels for better transcription"""
        
        if output_path is None:
            temp_dir = Path(tempfile.gettempdir()) / "ums_chunking"
            temp_dir.mkdir(exist_ok=True)
            output_path = temp_dir / f"{input_path.stem}_normalized.wav"
        
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-af", "loudnorm",  # Loudness normalization
            "-ar", "16000",  # Sample rate
            "-ac", "1",  # Mono
            "-y",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            logger.debug(f"Audio normalization completed: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"Audio normalization failed: {e}")
            return input_path  # Return original if normalization fails
    
    def remove_silence(self, input_path: Path, silence_threshold: str = "-30dB", 
                      min_silence_duration: float = 0.5) -> Path:
        """Remove silence from audio file"""
        
        temp_dir = Path(tempfile.gettempdir()) / "ums_chunking"
        temp_dir.mkdir(exist_ok=True)
        output_path = temp_dir / f"{input_path.stem}_no_silence.wav"
        
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-af", f"silenceremove=start_periods=1:start_duration=1:start_threshold={silence_threshold}:detection=peak",
            "-y",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            logger.debug(f"Silence removal completed: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"Silence removal failed: {e}")
            return input_path  # Return original if silence removal fails
    
    def check_ffmpeg_installation(self) -> bool:
        """Check if ffmpeg is installed and accessible"""
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("FFmpeg is available")
                return True
        except FileNotFoundError:
            pass
        
        logger.error("FFmpeg not found. Please install ffmpeg.")
        return False
    
    def check_ffprobe_installation(self) -> bool:
        """Check if ffprobe is installed and accessible"""
        try:
            result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("FFprobe is available")
                return True
        except FileNotFoundError:
            pass
        
        logger.error("FFprobe not found. Please install ffprobe.")
        return False
    
    def get_installation_instructions(self) -> str:
        """Get installation instructions for ffmpeg"""
        return """
FFmpeg Installation Instructions:

Windows:
- Download from https://ffmpeg.org/download.html
- Extract and add to PATH
- Or use: winget install ffmpeg

macOS:
- brew install ffmpeg

Linux (Ubuntu/Debian):
- sudo apt update
- sudo apt install ffmpeg

Linux (CentOS/RHEL):
- sudo yum install ffmpeg
- Or: sudo dnf install ffmpeg
        """
