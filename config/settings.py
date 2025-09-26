"""
Configuration settings for the Umsetzer Chunking Pipeline
"""

import os
from typing import Dict, Any, Optional

# Handle different pydantic versions
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    try:
        from pydantic import BaseSettings, Field
    except ImportError:
        # Create a simple BaseSettings fallback
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Simple Field fallback
        def Field(default=None, description=None, **kwargs):
            return default


class ChunkingConfig(BaseSettings):
    """Configuration for text chunking strategies"""
    
    # Chunking parameters based on Chroma Research
    max_chunk_size: int = Field(default=400, description="Maximum chunk size in characters")
    min_chunk_size: int = Field(default=100, description="Minimum chunk size in characters")
    overlap: int = Field(default=50, description="Overlap between chunks in characters")
    semantic_threshold: float = Field(default=0.7, description="Semantic similarity threshold")
    
    # Chunking strategy
    chunking_strategy: str = Field(default="semantic", description="Chunking strategy: semantic, recursive, or fixed")
    
    class Config:
        env_prefix = "CHUNKING_"


class EmbeddingConfig(BaseSettings):
    """Configuration for embedding generation"""
    
    # OpenAI settings
    openai_api_key: str = Field(..., description="OpenAI API key")
    embedding_model: str = Field(default="text-embedding-3-large", description="OpenAI embedding model")
    embedding_dimension: int = Field(default=3072, description="Embedding dimension")
    
    # Batch processing
    batch_size: int = Field(default=100, description="Batch size for embedding generation")
    
    class Config:
        env_prefix = "EMBEDDING_"


class DatabaseConfig(BaseSettings):
    """Configuration for Supabase database"""
    
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")
    supabase_service_key: str = Field(..., description="Supabase service role key")
    
    # Database settings
    table_name: str = Field(default="video_chunks", description="Table name for storing chunks")
    
    class Config:
        env_prefix = "DB_"


class TranscriptionConfig(BaseSettings):
    """Configuration for video transcription"""
    
    # Whisper settings
    whisper_model: str = Field(default="whisper-1", description="OpenAI Whisper model")
    language: str = Field(default="de", description="Language for transcription")
    
    # Audio processing
    sample_rate: int = Field(default=16000, description="Audio sample rate")
    max_audio_duration: int = Field(default=3600, description="Max audio duration in seconds")
    
    class Config:
        env_prefix = "TRANSCRIPTION_"


class AgentConfig(BaseSettings):
    """Configuration for RAG agent"""
    
    # LLM settings
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model for responses")
    temperature: float = Field(default=0.1, description="LLM temperature")
    max_tokens: int = Field(default=1000, description="Max response tokens")
    
    # Retrieval settings
    top_k: int = Field(default=5, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.7, description="Minimum similarity threshold")
    
    class Config:
        env_prefix = "AGENT_"


class Settings(BaseSettings):
    """Main settings class combining all configurations"""

    # OpenAI Configuration (directly in main settings)
    openai_api_key: str = Field(..., description="OpenAI API key")

    # Supabase Configuration (New API Keys - Recommended)
    supabase_url: Optional[str] = Field(default=None, description="Supabase project URL")
    supabase_publishable_key: Optional[str] = Field(default=None, description="Supabase publishable key")
    supabase_secret_key: Optional[str] = Field(default=None, description="Supabase secret key")
    
    # Legacy Supabase Configuration (Deprecated)
    supabase_anon_key: Optional[str] = Field(default=None, description="Legacy Supabase anon key")
    supabase_service_role_key: Optional[str] = Field(default=None, description="Legacy Supabase service role key")

    # Chunking Configuration
    chunking_max_chunk_size: int = Field(default=400, description="Maximum chunk size")
    chunking_min_chunk_size: int = Field(default=100, description="Minimum chunk size")
    chunking_overlap: int = Field(default=50, description="Overlap between chunks")
    chunking_semantic_threshold: float = Field(default=0.7, description="Semantic similarity threshold")
    chunking_strategy: str = Field(default="semantic", description="Chunking strategy")

    # Embedding Configuration
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")
    embedding_dimension: int = Field(default=1536, description="Embedding dimensions")
    embedding_batch_size: int = Field(default=100, description="Embedding batch size")

    # Agent Configuration
    agent_llm_model: str = Field(default="gpt-4o-mini", description="LLM model for agent")
    agent_temperature: float = Field(default=0.1, description="LLM temperature")
    agent_max_tokens: int = Field(default=1000, description="Max tokens for LLM")
    agent_top_k: int = Field(default=5, description="Top K chunks for context")
    agent_similarity_threshold: float = Field(default=0.7, description="Similarity threshold")

    # Database Configuration
    db_table_name: str = Field(default="video_chunks", description="Database table name")

    # Transcription Configuration
    transcription_whisper_model: str = Field(default="whisper-1", description="Whisper model")
    transcription_language: str = Field(default="de", description="Language for transcription")
    transcription_sample_rate: int = Field(default=16000, description="Audio sample rate")
    transcription_max_audio_duration: int = Field(default=3600, description="Max audio duration")

    # General settings
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""


# Global settings instance
settings = Settings()
