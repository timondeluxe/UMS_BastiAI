"""
Embedding generation and Supabase integration for video chunks
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import uuid
from dataclasses import asdict

from openai import OpenAI
from supabase import create_client, Client
from config.settings import settings
from src.chunking.semantic_chunker import Chunk


logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text chunks using OpenAI"""
    
    def __init__(self):
        """Initialize embedding generator"""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = "text-embedding-3-small"  # Compatible with pgvector limits
        self.dimensions = 1536  # Dimensions for text-embedding-3-small
        
        logger.info(f"Initialized EmbeddingGenerator with model: {self.model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text chunk
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise


class SupabaseClient:
    """Client for Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        # Try new API keys first, fallback to legacy
        supabase_url = getattr(settings, 'supabase_url', None)
        supabase_publishable_key = getattr(settings, 'supabase_publishable_key', None)
        supabase_secret_key = getattr(settings, 'supabase_secret_key', None)
        
        # Legacy keys (deprecated)
        supabase_anon_key = getattr(settings, 'supabase_anon_key', None)
        supabase_service_role_key = getattr(settings, 'supabase_service_role_key', None)
        
        if not supabase_url:
            logger.warning("Supabase URL not found. Using mock client.")
            self.client = None
            self.mock_mode = True
        elif supabase_publishable_key and supabase_secret_key:
            # Use new API keys (recommended)
            self.client: Client = create_client(supabase_url, supabase_secret_key)
            self.mock_mode = False
            logger.info("Using new Supabase API keys (sb_publishable_... and sb_secret_...)")
        elif supabase_anon_key and supabase_service_role_key:
            # Use legacy API keys (deprecated)
            self.client: Client = create_client(supabase_url, supabase_service_role_key)
            self.mock_mode = False
            logger.warning("Using legacy Supabase API keys (anon/service_role). Please migrate to new keys by November 2025.")
        else:
            logger.warning("Supabase credentials not found. Using mock client.")
            self.client = None
            self.mock_mode = True
        
        logger.info(f"Initialized SupabaseClient (mock_mode: {self.mock_mode})")
    
    def create_video_chunks_table(self):
        """Create the video_chunks table if it doesn't exist"""
        if self.mock_mode:
            logger.info("Mock mode: Skipping table creation")
            return
        
        try:
            # This would normally be done via Supabase SQL editor
            # For now, we'll assume the table exists
            logger.info("Assuming video_chunks table exists")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise
    
    def insert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> bool:
        """
        Insert chunks with embeddings into Supabase
        
        Args:
            chunks: List of chunks to insert
            embeddings: Corresponding embeddings
            
        Returns:
            True if successful
        """
        if self.mock_mode:
            logger.info(f"Mock mode: Would insert {len(chunks)} chunks")
            return self._mock_insert_chunks(chunks, embeddings)
        
        try:
            # Check for existing chunks to avoid duplicates
            existing_chunks = self._check_existing_chunks(chunks)
            
            # Filter out existing chunks
            new_chunks = []
            new_embeddings = []
            
            for chunk, embedding in zip(chunks, embeddings):
                chunk_key = f"{chunk.video_id}_{chunk.chunk_index}"
                if chunk_key not in existing_chunks:
                    new_chunks.append(chunk)
                    new_embeddings.append(embedding)
                else:
                    logger.info(f"Skipping existing chunk: {chunk_key}")
            
            if not new_chunks:
                logger.info("All chunks already exist, nothing to insert")
                return True
            
            # Prepare data for insertion
            records = []
            for chunk, embedding in zip(new_chunks, new_embeddings):
                record = {
                    "id": str(uuid.uuid4()),
                    "video_id": chunk.video_id,
                    "chunk_text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                    "start_timestamp": chunk.start_timestamp,
                    "end_timestamp": chunk.end_timestamp,
                    "embedding": embedding,
                    "metadata": chunk.metadata
                }
                records.append(record)
            
            # Insert in batches (Supabase has limits)
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                result = self.client.table("video_chunks").insert(batch).execute()
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} chunks")
            
            logger.info(f"Successfully inserted {len(new_chunks)} new chunks (skipped {len(chunks) - len(new_chunks)} existing)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert chunks: {e}")
            return False
    
    def _mock_insert_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> bool:
        """Mock implementation for testing without Supabase"""
        
        # Save to local JSON file for testing
        mock_data = {
            "chunks": [asdict(chunk) for chunk in chunks],
            "embeddings": embeddings,
            "total_chunks": len(chunks),
            "total_embeddings": len(embeddings)
        }
        
        mock_file = Path("mock_supabase_data.json")
        with open(mock_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Mock data saved to: {mock_file}")
        return True
    
    def search_similar_chunks(self, query_embedding: List[float], 
                           video_id: Optional[str] = None, 
                           limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using hybrid approach: embedding similarity + keyword matching
        
        Args:
            query_embedding: Query embedding vector
            video_id: Optional video ID filter
            limit: Number of results to return
            
        Returns:
            List of similar chunks with metadata
        """
        if self.mock_mode:
            logger.info("Mock mode: Would search similar chunks")
            return self._mock_search_chunks(query_embedding, video_id, limit)
        
        try:
            # Build query
            query = self.client.table("video_chunks").select("*")
            
            if video_id:
                query = query.eq("video_id", video_id)
            
            # Get all chunks for hybrid search
            all_chunks = query.execute()
            
            if not all_chunks.data:
                logger.warning("No chunks found in database")
                return []
            
            logger.info(f"Using pure vector similarity search on {len(all_chunks.data)} chunks")
            
            # Calculate cosine similarity for all chunks
            similarities = []
            for chunk in all_chunks.data:
                if chunk.get('embedding'):
                    try:
                        chunk_embedding = chunk['embedding']
                        if isinstance(chunk_embedding, str):
                            # Parse string representation
                            chunk_embedding = [float(x) for x in chunk_embedding.strip('[]').split(',')]
                        
                        # Calculate cosine similarity
                        similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                        similarities.append((chunk, similarity))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not parse embedding for chunk {chunk.get('id', 'unknown')}: {e}")
                        continue
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Take top results
            top_chunks = [chunk for chunk, sim in similarities[:limit]]
            
            if similarities:
                logger.info(f"Found {len(top_chunks)} similar chunks (top similarity: {similarities[0][1]:.3f})")
            else:
                logger.warning("No chunks with valid embeddings found")
            
            return top_chunks
            
        except Exception as e:
            logger.error(f"Failed to search chunks: {e}")
            return []
    
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _mock_search_chunks(self, query_embedding: List[float], 
                          video_id: Optional[str] = None, 
                          limit: int = 5) -> List[Dict[str, Any]]:
        """Mock search implementation"""
        
        # Load mock data
        mock_file = Path("mock_supabase_data.json")
        if not mock_file.exists():
            logger.warning("No mock data found")
            return []
        
        with open(mock_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = data.get("chunks", [])
        
        # Filter by video_id if specified
        if video_id:
            chunks = [c for c in chunks if c.get("video_id") == video_id]
        
        # Return first N chunks (in real implementation, this would use vector similarity)
        # Format chunks to match expected structure
        formatted_chunks = []
        for chunk in chunks[:limit]:
            formatted_chunk = {
                "chunk_text": chunk.get("text", ""),
                "start_timestamp": chunk.get("start_timestamp", 0),
                "end_timestamp": chunk.get("end_timestamp", 0),
                "video_id": chunk.get("video_id", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "metadata": chunk.get("metadata", {})
            }
            formatted_chunks.append(formatted_chunk)
        
        return formatted_chunks
    
    def _check_existing_chunks(self, chunks: List[Chunk]) -> set:
        """
        Check which chunks already exist in the database
        
        This method uses a two-tier approach:
        1. First check by video_id (fast)
        2. If video exists, check by content hash (robust)
        
        Args:
            chunks: List of chunks to check
            
        Returns:
            Set of existing chunk keys (video_id_chunk_index)
        """
        if not chunks:
            return set()
        
        existing_chunks = set()
        
        try:
            # Get unique video IDs
            video_ids = list(set(chunk.video_id for chunk in chunks))
            
            for video_id in video_ids:
                # Check if video already exists in database
                video_result = self.client.table("video_chunks").select("video_id").eq("video_id", video_id).limit(1).execute()
                
                if video_result.data:
                    # Video exists - check all chunks for this video
                    logger.info(f"Video {video_id} already exists in database. Checking for duplicate chunks...")
                    
                    # Get all existing chunks for this video
                    result = self.client.table("video_chunks").select("video_id, chunk_index, chunk_text").eq("video_id", video_id).execute()
                    
                    # Create a mapping of existing chunks by content hash
                    existing_content_hashes = {}
                    for row in result.data:
                        content_hash = self._get_content_hash(row['chunk_text'])
                        existing_content_hashes[content_hash] = f"{row['video_id']}_{row['chunk_index']}"
                    
                    # Check each new chunk against existing content
                    for chunk in chunks:
                        if chunk.video_id == video_id:
                            content_hash = self._get_content_hash(chunk.text)
                            if content_hash in existing_content_hashes:
                                existing_chunks.add(existing_content_hashes[content_hash])
                    
                    logger.info(f"Video {video_id}: Found {len(existing_content_hashes)} existing chunks, {len([c for c in chunks if c.video_id == video_id])} new chunks")
                else:
                    logger.info(f"Video {video_id} not found in database. All chunks will be new.")
            
            logger.info(f"Total existing chunks found: {len(existing_chunks)} (video + content-based detection)")
            return existing_chunks
            
        except Exception as e:
            logger.warning(f"Could not check existing chunks: {e}")
            return set()
    
    def _get_content_hash(self, text: str) -> str:
        """
        Generate a hash for chunk content to detect duplicates
        
        Args:
            text: Chunk text content
            
        Returns:
            Hash string for content comparison
        """
        import hashlib
        
        # Normalize text (remove extra whitespace, convert to lowercase)
        normalized_text = " ".join(text.strip().lower().split())
        
        # Generate hash
        content_hash = hashlib.md5(normalized_text.encode('utf-8')).hexdigest()
        
        return content_hash


class VideoProcessor:
    """Main processor for video transcription, chunking, and embedding"""
    
    def __init__(self):
        """Initialize video processor"""
        self.embedding_generator = EmbeddingGenerator()
        self.supabase_client = SupabaseClient()
        
        logger.info("Initialized VideoProcessor")
    
    def process_video_chunks(self, chunks: List[Chunk]) -> bool:
        """
        Process chunks: generate embeddings and store in Supabase
        
        Args:
            chunks: List of chunks to process
            
        Returns:
            True if successful
        """
        logger.info(f"Processing {len(chunks)} chunks")
        
        try:
            # Generate embeddings
            logger.info("Generating embeddings...")
            texts = [chunk.text for chunk in chunks]
            embeddings = self.embedding_generator.generate_embeddings_batch(texts)
            
            # Store in Supabase
            logger.info("Storing chunks in Supabase...")
            success = self.supabase_client.insert_chunks(chunks, embeddings)
            
            if success:
                logger.info("✅ Video processing completed successfully")
                return True
            else:
                logger.error("❌ Failed to store chunks")
                return False
                
        except Exception as e:
            logger.error(f"❌ Video processing failed: {e}")
            return False
    
    def search_video_content(self, query: str, video_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search video content using pure vector similarity
        
        Args:
            query: Natural language search query
            video_id: Optional video ID filter
            
        Returns:
            List of relevant chunks
        """
        logger.info(f"Searching for: '{query}'")
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_generator.generate_embedding(query)
            
            # Search similar chunks using pure vector similarity
            results = self.supabase_client.search_similar_chunks(
                query_embedding, video_id, limit=40
            )
            
            logger.info(f"Found {len(results)} relevant chunks using vector similarity")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
