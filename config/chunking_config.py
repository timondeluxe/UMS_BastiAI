"""
Chunking configuration based on Chroma Research findings
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ChunkingStrategy:
    """Configuration for different chunking strategies"""
    
    name: str
    max_chunk_size: int
    min_chunk_size: int
    overlap: int
    semantic_threshold: float
    description: str


# Chunking strategies based on Chroma Research
CHUNKING_STRATEGIES = {
    "semantic": ChunkingStrategy(
        name="semantic",
        max_chunk_size=400,
        min_chunk_size=100,
        overlap=50,
        semantic_threshold=0.7,
        description="Semantic chunking with 89.7% recall (Chroma Research)"
    ),
    
    "recursive": ChunkingStrategy(
        name="recursive",
        max_chunk_size=500,
        min_chunk_size=100,
        overlap=50,
        semantic_threshold=0.0,
        description="Recursive character splitting (baseline)"
    ),
    
    "fixed": ChunkingStrategy(
        name="fixed",
        max_chunk_size=400,
        min_chunk_size=400,
        overlap=0,
        semantic_threshold=0.0,
        description="Fixed-size chunking"
    ),
    
    "video_optimized": ChunkingStrategy(
        name="video_optimized",
        max_chunk_size=600,
        min_chunk_size=150,
        overlap=75,
        semantic_threshold=0.75,
        description="Optimized for video transcripts with speaker changes"
    )
}


def get_chunking_strategy(strategy_name: str = "semantic") -> ChunkingStrategy:
    """Get chunking strategy configuration"""
    if strategy_name not in CHUNKING_STRATEGIES:
        raise ValueError(f"Unknown chunking strategy: {strategy_name}")
    return CHUNKING_STRATEGIES[strategy_name]


def get_optimal_strategy_for_content(content_type: str) -> ChunkingStrategy:
    """Get optimal chunking strategy based on content type"""
    
    strategies = {
        "video_transcript": "video_optimized",
        "meeting_recording": "video_optimized", 
        "presentation": "semantic",
        "general_text": "semantic",
        "code": "recursive",
        "documentation": "semantic"
    }
    
    strategy_name = strategies.get(content_type, "semantic")
    return get_chunking_strategy(strategy_name)


# Performance benchmarks from Chroma Research
PERFORMANCE_BENCHMARKS = {
    "semantic": {
        "recall_mean": 0.897,
        "recall_std": 0.290,
        "iou_mean": 0.183,
        "iou_std": 0.128
    },
    "recursive": {
        "recall_mean": 0.809,
        "recall_std": 0.379,
        "iou_mean": 0.106,
        "iou_std": 0.106
    }
}
