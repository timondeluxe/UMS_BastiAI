"""
Test script for embedding generation and Supabase integration
"""

import logging
from pathlib import Path
import sys
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embedding.embedding_generator import EmbeddingGenerator, SupabaseClient, VideoProcessor
from src.chunking.semantic_chunker import SemanticChunker
from src.utils.transcription_utils import load_transcription_as_result, list_transcriptions


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_embedding_generation():
    """Test embedding generation with sample text"""
    
    print("🧪 Testing Embedding Generation")
    print("=" * 50)
    
    # Initialize embedding generator
    generator = EmbeddingGenerator()
    
    # Test with sample texts
    sample_texts = [
        "Hallo, willkommen zum Performance Call.",
        "Heute sprechen wir über wichtige Themen.",
        "Die Performance hat sich deutlich verbessert."
    ]
    
    print(f"📝 Generating embeddings for {len(sample_texts)} sample texts...")
    
    try:
        # Generate embeddings
        embeddings = generator.generate_embeddings_batch(sample_texts)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"📊 Embedding dimensions: {len(embeddings[0])}")
        
        # Show first few values of first embedding
        first_embedding = embeddings[0][:5]
        print(f"🔢 Sample values: {first_embedding}")
        
        return embeddings
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        return None


def test_supabase_client():
    """Test Supabase client (mock mode)"""
    
    print(f"\n🧪 Testing Supabase Client")
    print("-" * 40)
    
    # Initialize Supabase client
    client = SupabaseClient()
    
    print(f"📊 Supabase client initialized (mock_mode: {client.mock_mode})")
    
    # Test table creation
    print("🔧 Testing table creation...")
    client.create_video_chunks_table()
    
    print("✅ Supabase client test completed")


def test_full_video_processing():
    """Test complete video processing pipeline"""
    
    print(f"\n🧪 Testing Full Video Processing Pipeline")
    print("=" * 60)
    
    # Load available transcriptions
    transcriptions = list_transcriptions()
    if not transcriptions:
        print("❌ No transcriptions found. Run transcription test first.")
        return
    
    # Use the first available transcription
    video_id = transcriptions[0]
    print(f"📹 Processing video: {video_id}")
    
    # Load transcription
    transcription_result = load_transcription_as_result(video_id)
    if not transcription_result:
        print(f"❌ Could not load transcription: {video_id}")
        return
    
    print(f"📊 Transcription loaded: {len(transcription_result.segments)} segments")
    
    # Create chunks using semantic chunking
    print("🔧 Creating semantic chunks...")
    chunker = SemanticChunker(strategy="semantic")
    chunks = chunker.chunk_transcription(transcription_result.segments, video_id)
    
    print(f"✅ Created {len(chunks)} chunks")
    
    # Process chunks (generate embeddings and store)
    print("🚀 Processing chunks (embeddings + storage)...")
    processor = VideoProcessor()
    
    # Process only first 5 chunks for testing (to save API costs)
    test_chunks = chunks[:5]
    print(f"📝 Processing {len(test_chunks)} chunks for testing...")
    
    success = processor.process_video_chunks(test_chunks)
    
    if success:
        print("✅ Video processing completed successfully!")
        
        # Test search functionality
        print(f"\n🔍 Testing search functionality...")
        search_results = processor.search_video_content(
            "Performance Call", video_id
        )
        
        print(f"📊 Search results: {len(search_results)} chunks found")
        
        if search_results:
            print(f"📝 First result:")
            first_result = search_results[0]
            print(f"   Text: {first_result.get('chunk_text', '')[:100]}...")
            print(f"   Timestamp: {first_result.get('start_timestamp', 0):.1f}s")
        
    else:
        print("❌ Video processing failed")


def test_embedding_costs():
    """Estimate embedding generation costs"""
    
    print(f"\n💰 Embedding Cost Estimation")
    print("-" * 40)
    
    # Load transcription to estimate costs
    transcriptions = list_transcriptions()
    if not transcriptions:
        print("❌ No transcriptions found")
        return
    
    video_id = transcriptions[0]
    transcription_result = load_transcription_as_result(video_id)
    
    if not transcription_result:
        print(f"❌ Could not load transcription: {video_id}")
        return
    
    # Create chunks
    chunker = SemanticChunker(strategy="semantic")
    chunks = chunker.chunk_transcription(transcription_result.segments, video_id)
    
    # Calculate costs
    total_chunks = len(chunks)
    total_characters = sum(len(chunk.text) for chunk in chunks)
    
    # OpenAI pricing (as of 2024)
    # text-embedding-3-large: $0.00013 per 1K tokens
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = total_characters / 4
    cost_per_1k_tokens = 0.00013
    estimated_cost = (estimated_tokens / 1000) * cost_per_1k_tokens
    
    print(f"📊 Cost Estimation for 1 video:")
    print(f"   Chunks: {total_chunks}")
    print(f"   Characters: {total_characters:,}")
    print(f"   Estimated tokens: {estimated_tokens:,.0f}")
    print(f"   Estimated cost: ${estimated_cost:.4f}")
    
    # Estimate for 300 videos
    cost_300_videos = estimated_cost * 300
    print(f"\n📊 Cost Estimation for 300 videos:")
    print(f"   Estimated total cost: ${cost_300_videos:.2f}")


def main():
    """Main test function"""
    
    print("🧪 Testing Umsetzer Embedding Generation")
    print("=" * 60)
    
    # Test 1: Basic embedding generation
    embeddings = test_embedding_generation()
    
    # Test 2: Supabase client
    test_supabase_client()
    
    # Test 3: Cost estimation
    test_embedding_costs()
    
    # Test 4: Full pipeline (only if embeddings worked)
    if embeddings:
        test_full_video_processing()
    
    print(f"\n🎉 Embedding tests completed!")
    print(f"\n💡 Next steps:")
    print(f"   1. Set up Supabase credentials in .env file")
    print(f"   2. Create video_chunks table in Supabase")
    print(f"   3. Process all chunks for the test video")
    print(f"   4. Build the mini-chat agent")


if __name__ == "__main__":
    main()
