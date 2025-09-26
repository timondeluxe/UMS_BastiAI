"""
CLI Script for Batch Video Processing
"""

import argparse
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from batch_processor import BatchVideoProcessor
from src.chunking.semantic_chunker import SemanticChunker


def main():
    """CLI for batch video processing"""
    
    parser = argparse.ArgumentParser(
        description="Umsetzer Batch Video Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all videos in a directory
  python batch_processor.py --directory videos/
  
  # Process specific video files
  python batch_processor.py --files video1.mp4 video2.mp4
  
  # Process with custom output directory
  python batch_processor.py --directory videos/ --output transcriptions/
  
  # Process with different chunking strategy
  python batch_processor.py --directory videos/ --chunking-strategy video_optimized
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--directory", "-d",
        type=Path,
        help="Directory containing video files to process"
    )
    input_group.add_argument(
        "--files", "-f",
        nargs="+",
        type=Path,
        help="Specific video files to process"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output directory for transcriptions (optional)"
    )
    
    # Processing options
    parser.add_argument(
        "--chunking-strategy",
        choices=["semantic", "recursive", "video_optimized", "fixed"],
        default="semantic",
        help="Chunking strategy to use (default: semantic)"
    )
    
    parser.add_argument(
        "--max-videos",
        type=int,
        help="Maximum number of videos to process (for testing)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually processing"
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = BatchVideoProcessor()
    
    # Set chunking strategy
    processor.chunker = SemanticChunker(strategy=args.chunking_strategy)
    
    print("🚀 Umsetzer Batch Video Processor")
    print("=" * 50)
    print(f"Chunking strategy: {args.chunking_strategy}")
    
    if args.directory:
        # Process directory
        if not args.directory.exists():
            print(f"❌ Directory not found: {args.directory}")
            return
        
        # Find video files
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(args.directory.glob(f"*{ext}"))
            video_files.extend(args.directory.glob(f"*{ext.upper()}"))
        
        # Remove duplicates (case-insensitive)
        video_files = list(set(video_files))
        
        if not video_files:
            print(f"❌ No video files found in {args.directory}")
            return
        
        # Limit videos if specified
        if args.max_videos:
            video_files = video_files[:args.max_videos]
        
        print(f"📁 Found {len(video_files)} video files")
        
        if args.dry_run:
            print("🔍 Dry run - would process:")
            for video_file in video_files:
                print(f"   - {video_file.name}")
            return
        
        # Process videos
        stats = processor.process_video_directory(args.directory, args.output)
        
    elif args.files:
        # Process specific files
        # Check if files exist
        existing_files = []
        for video_file in args.files:
            if video_file.exists():
                existing_files.append(video_file)
            else:
                print(f"⚠️  File not found: {video_file}")
        
        if not existing_files:
            print("❌ No valid video files found")
            return
        
        # Limit videos if specified
        if args.max_videos:
            existing_files = existing_files[:args.max_videos]
        
        print(f"📁 Processing {len(existing_files)} specific video files")
        
        if args.dry_run:
            print("🔍 Dry run - would process:")
            for video_file in existing_files:
                print(f"   - {video_file.name}")
            return
        
        # Process videos
        stats = processor.process_video_list(existing_files, args.output)
    
    # Print final results
    print(f"\n🎉 Batch processing completed!")
    print(f"✅ {stats['processed_videos']} videos processed successfully")
    print(f"❌ {stats['failed_videos']} videos failed")
    print(f"📊 Total chunks created: {stats['total_chunks']}")
    print(f"💰 Estimated cost: ${stats['total_cost']:.4f}")
    print(f"⏱️  Processing time: {stats['processing_time']:.1f} seconds")
    
    if stats['total_videos'] > 0:
        success_rate = (stats['processed_videos'] / stats['total_videos']) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")


if __name__ == "__main__":
    main()
