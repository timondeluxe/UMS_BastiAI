"""
Batch Processing Script for Multiple Videos
"""

import logging
from pathlib import Path
import sys
import os
from typing import List, Dict, Any
import time

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embedding.embedding_generator import VideoProcessor
from src.chunking.semantic_chunker import SemanticChunker
from src.transcription.whisper_client import WhisperClient
from src.utils.transcription_utils import list_transcriptions


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BatchVideoProcessor:
    """Batch processor for multiple videos"""
    
    def __init__(self):
        """Initialize batch processor"""
        self.whisper = WhisperClient()
        self.chunker = SemanticChunker(strategy="semantic")
        self.processor = VideoProcessor()
        
        # Statistics
        self.stats = {
            "total_videos": 0,
            "processed_videos": 0,
            "skipped_videos": 0,
            "failed_videos": 0,
            "total_chunks": 0,
            "total_cost": 0.0,
            "processing_time": 0.0
        }
        
        logger.info("Initialized BatchVideoProcessor")
    
    def process_video_directory(self, video_directory: Path, 
                              output_directory: Path = None) -> Dict[str, Any]:
        """
        Process all videos in a directory
        
        Args:
            video_directory: Path to directory containing videos
            output_directory: Path to save transcriptions (optional)
            
        Returns:
            Processing statistics
        """
        logger.info(f"Processing videos in: {video_directory}")
        
        # Find all video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(video_directory.glob(f"*{ext}"))
            video_files.extend(video_directory.glob(f"*{ext.upper()}"))
        
        # Remove duplicates (case-insensitive)
        video_files = list(set(video_files))
        
        if not video_files:
            logger.warning(f"No video files found in {video_directory}")
            return self.stats
        
        logger.info(f"Found {len(video_files)} video files")
        
        # Create output directory if specified
        if output_directory:
            output_directory.mkdir(parents=True, exist_ok=True)
        
        # Process each video
        start_time = time.time()
        
        for i, video_file in enumerate(video_files, 1):
            logger.info(f"Processing video {i}/{len(video_files)}: {video_file.name}")
            
            try:
                result = self._process_single_video(video_file, output_directory)
                
                if result == "processed":
                    self.stats["processed_videos"] += 1
                    logger.info(f"✅ Successfully processed: {video_file.name}")
                elif result == "skipped":
                    self.stats["skipped_videos"] += 1
                    logger.info(f"⏭️ Skipped (already exists): {video_file.name}")
                else:
                    self.stats["failed_videos"] += 1
                    logger.error(f"❌ Failed to process: {video_file.name}")
                
            except Exception as e:
                self.stats["failed_videos"] += 1
                logger.error(f"❌ Error processing {video_file.name}: {e}")
            
            # Add delay to avoid rate limiting
            if i < len(video_files):
                time.sleep(2)
        
        # Calculate final statistics
        self.stats["total_videos"] = len(video_files)
        self.stats["processing_time"] = time.time() - start_time
        
        logger.info(f"Batch processing completed!")
        self._print_statistics()
        
        return self.stats
    
    def process_video_list(self, video_files: List[Path], 
                          output_directory: Path = None) -> Dict[str, Any]:
        """
        Process a list of specific video files
        
        Args:
            video_files: List of video file paths
            output_directory: Path to save transcriptions (optional)
            
        Returns:
            Processing statistics
        """
        logger.info(f"Processing {len(video_files)} specific videos")
        
        # Create output directory if specified
        if output_directory:
            output_directory.mkdir(parents=True, exist_ok=True)
        
        # Process each video
        start_time = time.time()
        
        for i, video_file in enumerate(video_files, 1):
            logger.info(f"Processing video {i}/{len(video_files)}: {video_file.name}")
            
            try:
                result = self._process_single_video(video_file, output_directory)
                
                if result == "processed":
                    self.stats["processed_videos"] += 1
                    logger.info(f"✅ Successfully processed: {video_file.name}")
                elif result == "skipped":
                    self.stats["skipped_videos"] += 1
                    logger.info(f"⏭️ Skipped (already exists): {video_file.name}")
                else:
                    self.stats["failed_videos"] += 1
                    logger.error(f"❌ Failed to process: {video_file.name}")
                
            except Exception as e:
                self.stats["failed_videos"] += 1
                logger.error(f"❌ Error processing {video_file.name}: {e}")
            
            # Add delay to avoid rate limiting
            if i < len(video_files):
                time.sleep(2)
        
        # Calculate final statistics
        self.stats["total_videos"] = len(video_files)
        self.stats["processing_time"] = time.time() - start_time
        
        logger.info(f"Batch processing completed!")
        self._print_statistics()
        
        return self.stats
    
    def _process_single_video(self, video_file: Path, 
                            output_directory: Path = None) -> bool:
        """
        Process a single video file
        
        Args:
            video_file: Path to video file
            output_directory: Directory to save transcription (optional)
            
        Returns:
            True if successful
        """
        try:
            # Step 1: Check if video already exists in database
            video_id = self.whisper._generate_video_id(video_file)
            
            # Check if video already exists in database
            existing_check = self.processor.supabase_client.client.table("video_chunks").select("video_id").eq("video_id", video_id).limit(1).execute()
            
            if existing_check.data:
                logger.info(f"Video {video_id} already exists in database. Skipping processing.")
                return "skipped"
            
            # Step 2: Transcribe video (only if not exists)
            logger.info(f"Transcribing: {video_file.name}")
            transcription_result = self.whisper.transcribe_video(video_file)
            
            # Save transcription if output directory specified
            if output_directory:
                transcription_file = output_directory / f"{transcription_result.video_id}.json"
                self._save_transcription(transcription_result, transcription_file)
            
            # Step 2: Create chunks
            logger.info(f"Chunking: {video_file.name}")
            chunks = self.chunker.chunk_transcription(
                transcription_result.segments, 
                transcription_result.video_id
            )
            
            self.stats["total_chunks"] += len(chunks)
            
            # Step 3: Process chunks (embeddings + storage)
            logger.info(f"Processing chunks: {video_file.name}")
            success = self.processor.process_video_chunks(chunks)
            
            if success:
                # Estimate cost (rough calculation)
                estimated_cost = self._estimate_cost(transcription_result, chunks)
                self.stats["total_cost"] += estimated_cost
            
            return "processed" if success else "failed"
            
        except Exception as e:
            logger.error(f"Error processing {video_file.name}: {e}")
            return "failed"
    
    def _save_transcription(self, transcription_result, output_file: Path):
        """Save transcription to JSON file"""
        import json
        
        transcription_data = {
            "video_id": transcription_result.video_id,
            "filename": output_file.stem,
            "duration": transcription_result.duration,
            "language": transcription_result.language,
            "segments": [
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "speaker": seg.speaker,
                    "confidence": seg.confidence
                } for seg in transcription_result.segments
            ],
            "metadata": {
                "word_count": transcription_result.metadata.get('word_count', 0),
                "character_count": transcription_result.metadata.get('character_count', 0),
                "segment_count": len(transcription_result.segments),
                "avg_speaking_rate": transcription_result.metadata.get('avg_speaking_rate', 0.0),
                "speakers": [
                    {
                        "name": speaker.name,
                        "segments_count": speaker.segments_count,
                        "total_duration": speaker.total_duration,
                        "word_count": speaker.word_count
                    } for speaker in transcription_result.metadata.get('speakers', [])
                ]
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transcription_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Transcription saved to: {output_file}")
    
    def _estimate_cost(self, transcription_result, chunks) -> float:
        """Estimate processing cost for a video"""
        # Rough cost estimation
        transcription_cost = 0.006  # $0.006 per hour
        embedding_cost = len(chunks) * 0.00001  # $0.00001 per chunk
        
        return transcription_cost + embedding_cost
    
    def _print_statistics(self):
        """Print processing statistics"""
        print(f"\n📊 Batch Processing Statistics:")
        print(f"=" * 50)
        print(f"Total videos: {self.stats['total_videos']}")
        print(f"Processed: {self.stats['processed_videos']}")
        print(f"Skipped: {self.stats['skipped_videos']}")
        print(f"Failed: {self.stats['failed_videos']}")
        print(f"Total chunks: {self.stats['total_chunks']}")
        print(f"Processing time: {self.stats['processing_time']:.1f} seconds")
        print(f"Estimated cost: ${self.stats['total_cost']:.4f}")
        
        if self.stats['total_videos'] > 0:
            success_rate = (self.stats['processed_videos'] / self.stats['total_videos']) * 100
            print(f"Success rate: {success_rate:.1f}%")


def main():
    """Main function for batch processing"""
    
    print("🚀 Umsetzer Batch Video Processor")
    print("=" * 50)
    
    # Example usage
    processor = BatchVideoProcessor()
    
    # Option 1: Process all videos in a directory
    video_directory = Path("videos/")  # Change this to your video directory
    
    if video_directory.exists():
        print(f"📁 Processing all videos in: {video_directory}")
        output_dir = Path("transcriptions/")
        
        stats = processor.process_video_directory(video_directory, output_dir)
        
        print(f"\n🎉 Batch processing completed!")
        print(f"✅ {stats['processed_videos']} videos processed successfully")
        print(f"❌ {stats['failed_videos']} videos failed")
        print(f"💰 Estimated cost: ${stats['total_cost']:.4f}")
        
    else:
        print(f"❌ Video directory not found: {video_directory}")
        print(f"💡 Create a 'videos/' directory and add your video files")
        
        # Option 2: Process specific video files
        print(f"\n📝 Alternative: Process specific files")
        print(f"   video_files = [Path('video1.mp4'), Path('video2.mp4')]")
        print(f"   processor.process_video_list(video_files)")


if __name__ == "__main__":
    main()
