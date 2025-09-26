"""
Test script for semantic chunking functionality
"""

import logging
from pathlib import Path
import sys
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chunking.semantic_chunker import SemanticChunker
from src.utils.transcription_utils import load_transcription_as_result, list_transcriptions
from config.chunking_config import CHUNKING_STRATEGIES


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_chunking_strategies():
    """Test different chunking strategies"""
    
    print("🧪 Testing Semantic Chunking Strategies")
    print("=" * 50)
    
    # Load available transcriptions
    transcriptions = list_transcriptions()
    if not transcriptions:
        print("❌ No transcriptions found. Run transcription test first.")
        return
    
    # Use the first available transcription
    video_id = transcriptions[0]
    print(f"📹 Using transcription: {video_id}")
    
    # Load transcription
    transcription_result = load_transcription_as_result(video_id)
    if not transcription_result:
        print(f"❌ Could not load transcription: {video_id}")
        return
    
    print(f"📊 Transcription loaded: {len(transcription_result.segments)} segments, "
          f"{transcription_result.metadata.get('word_count', 0)} words")
    
    # Test different strategies
    strategies = ["semantic", "recursive", "video_optimized", "fixed"]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n🔧 Testing {strategy} chunking...")
        
        try:
            # Initialize chunker
            chunker = SemanticChunker(strategy=strategy)
            
            # Create chunks
            chunks = chunker.chunk_transcription(
                transcription_result.segments, 
                video_id
            )
            
            # Get statistics
            stats = chunker.get_chunk_statistics(chunks)
            results[strategy] = {
                "chunks": chunks,
                "stats": stats
            }
            
            print(f"✅ {strategy}: {stats['total_chunks']} chunks, "
                  f"avg size: {stats['avg_chunk_size']:.1f} chars")
            
        except Exception as e:
            print(f"❌ {strategy} failed: {e}")
            logger.error(f"Chunking strategy {strategy} failed: {e}")
    
    # Compare results
    print(f"\n📊 Chunking Strategy Comparison:")
    print("-" * 60)
    print(f"{'Strategy':<15} {'Chunks':<8} {'Avg Size':<10} {'Total Words':<12}")
    print("-" * 60)
    
    for strategy, result in results.items():
        stats = result["stats"]
        print(f"{strategy:<15} {stats['total_chunks']:<8} "
              f"{stats['avg_chunk_size']:<10.1f} {stats['total_words']:<12}")
    
    # Show sample chunks from semantic strategy
    if "semantic" in results:
        print(f"\n📝 Sample Semantic Chunks:")
        print("-" * 40)
        
        semantic_chunks = results["semantic"]["chunks"]
        for i, chunk in enumerate(semantic_chunks[:3]):  # Show first 3 chunks
            print(f"\nChunk {i+1} [{chunk.start_timestamp:.1f}s - {chunk.end_timestamp:.1f}s]:")
            print(f"  Text: {chunk.text[:100]}...")
            print(f"  Words: {chunk.word_count}, Characters: {chunk.character_count}")
    
    return results


def test_chunking_with_custom_text():
    """Test chunking with custom text"""
    
    print(f"\n🧪 Testing Chunking with Custom Text")
    print("-" * 40)
    
    # Create mock segments for testing
    from src.transcription.whisper_client import TranscriptionSegment
    
    test_segments = [
        TranscriptionSegment(start=0.0, end=10.0, text="Hallo, willkommen zum Performance Call."),
        TranscriptionSegment(start=10.0, end=20.0, text="Heute sprechen wir über wichtige Themen."),
        TranscriptionSegment(start=20.0, end=30.0, text="Zunächst geht es um die aktuellen Zahlen."),
        TranscriptionSegment(start=30.0, end=40.0, text="Die Performance hat sich deutlich verbessert."),
        TranscriptionSegment(start=40.0, end=50.0, text="Das ist ein sehr positives Ergebnis für uns."),
    ]
    
    # Test semantic chunking
    chunker = SemanticChunker(strategy="semantic")
    chunks = chunker.chunk_transcription(test_segments, "test_video")
    
    print(f"Created {len(chunks)} chunks from {len(test_segments)} segments")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  Text: {chunk.text}")
        print(f"  Timestamps: {chunk.start_timestamp:.1f}s - {chunk.end_timestamp:.1f}s")
        print(f"  Words: {chunk.word_count}")


def main():
    """Main test function"""
    
    print("🧪 Testing Umsetzer Semantic Chunking")
    print("=" * 50)
    
    # Test 1: Chunking strategies with real transcription
    results = test_chunking_strategies()
    
    # Test 2: Custom text chunking
    test_chunking_with_custom_text()
    
    print(f"\n🎉 Chunking tests completed!")
    
    if results:
        print(f"\n💡 Recommendation:")
        semantic_stats = results.get("semantic", {}).get("stats", {})
        if semantic_stats:
            print(f"   Use 'semantic' strategy for best results:")
            print(f"   - {semantic_stats['total_chunks']} chunks")
            print(f"   - Average size: {semantic_stats['avg_chunk_size']:.1f} characters")
            print(f"   - Based on Chroma Research (89.7% recall)")


if __name__ == "__main__":
    main()
