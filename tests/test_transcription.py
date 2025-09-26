"""
Test script for video transcription functionality
"""

import logging
from pathlib import Path
import sys
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.transcription.whisper_client import WhisperClient
from src.transcription.audio_processor import AudioProcessor
from src.transcription.metadata_extractor import MetadataExtractor
from config.settings import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_audio_processor():
    """Test audio processing functionality"""
    logger.info("Testing AudioProcessor...")
    
    processor = AudioProcessor()
    
    # Test ffmpeg installation
    if not processor.check_ffmpeg_installation():
        logger.error("FFmpeg not installed. Please install ffmpeg first.")
        print(processor.get_installation_instructions())
        return False
    
    if not processor.check_ffprobe_installation():
        logger.error("FFprobe not installed. Please install ffprobe first.")
        return False
    
    logger.info("✅ AudioProcessor tests passed")
    return True


def test_whisper_client():
    """Test Whisper client functionality"""
    logger.info("Testing WhisperClient...")
    
    try:
        client = WhisperClient()
        
        # Test API connection
        if not client.test_connection():
            logger.error("OpenAI API connection failed. Check your API key.")
            return False
        
        logger.info("✅ WhisperClient tests passed")
        return True
        
    except Exception as e:
        logger.error(f"WhisperClient test failed: {e}")
        return False


def test_transcription_with_video(video_path: Path):
    """Test full transcription pipeline with actual video"""
    logger.info(f"Testing transcription with video: {video_path}")
    
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return False
    
    try:
        # Initialize components
        whisper_client = WhisperClient()
        metadata_extractor = MetadataExtractor()
        
        # Transcribe video
        logger.info("Starting transcription...")
        result = whisper_client.transcribe_video(video_path)
        
        # Extract metadata
        logger.info("Extracting metadata...")
        metadata = metadata_extractor.extract_metadata(result.segments, result.duration)
        
        # Save transcription to JSON file
        logger.info("Saving transcription...")
        import json
        transcription_data = {
            "video_id": result.video_id,
            "filename": video_path.name,
            "duration": result.duration,
            "language": result.language,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "speaker": seg.speaker,
                    "confidence": seg.confidence
                } for seg in result.segments
            ],
            "metadata": {
                "word_count": metadata.quality_metrics.get('total_words', 0),
                "character_count": metadata.quality_metrics.get('total_characters', 0),
                "segment_count": len(result.segments),
                "avg_speaking_rate": metadata.avg_speaking_rate,
                "speakers": [
                    {
                        "name": speaker.name,
                        "segments_count": speaker.segments_count,
                        "total_duration": speaker.total_duration,
                        "word_count": speaker.word_count
                    } for speaker in metadata.speakers
                ]
            }
        }
        
        transcription_file = Path("transcriptions") / f"{result.video_id}.json"
        with open(transcription_file, 'w', encoding='utf-8') as f:
            json.dump(transcription_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Transcription saved to: {transcription_file}")
        
        # Print results
        print(f"\n🎬 Transcription Results:")
        print(f"Video ID: {result.video_id}")
        print(f"Duration: {result.duration:.1f} seconds")
        print(f"Language: {result.language}")
        print(f"Segments: {len(result.segments)}")
        print(f"Total words: {metadata.quality_metrics.get('total_words', 0)}")
        print(f"Speakers: {len(metadata.speakers)}")
        
        print(f"\n👥 Speakers:")
        for speaker in metadata.speakers:
            print(f"  - {speaker.name}: {speaker.segments_count} segments, "
                  f"{speaker.total_duration:.1f}s, {speaker.word_count} words")
        
        print(f"\n📊 Quality Metrics:")
        print(f"  - Average confidence: {metadata.quality_metrics.get('avg_confidence', 'N/A')}")
        print(f"  - Average speaking rate: {metadata.avg_speaking_rate:.1f} words/min")
        print(f"  - Speaker changes: {metadata.speaker_changes}")
        
        print(f"\n📝 Sample Transcription (first 3 segments):")
        for i, segment in enumerate(result.segments[:3]):
            print(f"  {i+1}. [{segment.start:.1f}s - {segment.end:.1f}s] {segment.text}")
        
        logger.info("✅ Transcription test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Transcription test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 Testing Umsetzer Video Transcription Pipeline")
    print("=" * 50)
    
    # Test 1: Audio processor
    if not test_audio_processor():
        print("❌ Audio processor tests failed")
        return
    
    # Test 2: Whisper client
    if not test_whisper_client():
        print("❌ Whisper client tests failed")
        return
    
    # Test 3: Full transcription (if video provided)
    video_path = Path("umsetzer Performance Call ｜ Bastian Schmidt 2025-04-28 09_59_01 [1079321934].mp4")
    
    if video_path.exists():
        print(f"\n🎥 Found test video: {video_path}")
        if not test_transcription_with_video(video_path):
            print("❌ Transcription test failed")
            return
    else:
        print(f"\n⚠️  Test video not found: {video_path}")
        print("   Skipping full transcription test")
    
    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    main()
