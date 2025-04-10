"""
Utility to calculate dynamic token limits based on content length.

This module provides functions to scale token limits based on input content length,
ensuring that longer videos get proportionally more detailed responses.
"""

import math
from typing import Dict, Any, Optional, Union

def calculate_max_tokens(
    content_length: int, 
    content_type: str = "transcript",
    min_tokens: int = 200,
    max_tokens: int = 4000,
    base_tokens: Optional[int] = None
) -> int:
    """
    Calculate an appropriate max_tokens limit based on content length.
    
    Args:
        content_length (int): Length of the content in characters
        content_type (str): Type of content ('transcript', 'topic', etc.)
        min_tokens (int): Minimum token limit to return
        max_tokens (int): Maximum token limit to return
        base_tokens (int, optional): Base token limit to scale from (defaults vary by content_type)
        
    Returns:
        int: Calculated token limit
    """
    # Define default base tokens by content type if not specified
    if base_tokens is None:
        base_tokens_map = {
            "transcript": 1000,    # Default for transcript processing
            "topic": 500,          # Default for topic processing
            "qa": 800,             # Default for Q&A generation
            "summary": 1200,       # Default for summary generation
            "default": 1000        # Default fallback
        }
        base_tokens = base_tokens_map.get(content_type, base_tokens_map["default"])
    
    # Reference content lengths for scaling
    # These are approximate character counts for different video lengths
    reference_lengths = {
        "short": 5000,     # ~5 minute video
        "medium": 15000,   # ~15 minute video
        "long": 30000,     # ~30 minute video
        "very_long": 60000 # ~1 hour video
    }
    
    # Logarithmic scaling factor based on content length
    # This ensures that token limits don't grow linearly with content length
    # but rather increase more gradually for very long content
    if content_length <= reference_lengths["short"]:
        # For very short content, use base scaling
        scaling_factor = content_length / reference_lengths["short"]
    else:
        # For longer content, use logarithmic scaling
        log_factor = math.log(content_length / reference_lengths["short"]) / math.log(4)  # log base 4
        scaling_factor = 1.0 + log_factor
    
    # Calculate token limit with scaling factor
    token_limit = int(base_tokens * scaling_factor)
    
    # Ensure the token limit is within the specified bounds
    token_limit = max(min_tokens, min(token_limit, max_tokens))
    
    return token_limit


def get_token_limits_for_transcript(transcript_length: int) -> Dict[str, int]:
    """
    Calculate appropriate token limits for different operations based on transcript length.
    
    Args:
        transcript_length (int): Length of the transcript in characters
        
    Returns:
        Dict[str, int]: Dictionary mapping operation types to their token limits
    """
    return {
        "topic_extraction": calculate_max_tokens(
            transcript_length, 
            content_type="topic", 
            min_tokens=200, 
            max_tokens=1000
        ),
        "content_transformation": calculate_max_tokens(
            transcript_length, 
            content_type="transcript", 
            min_tokens=800, 
            max_tokens=4000
        ),
        "qa_generation": calculate_max_tokens(
            transcript_length, 
            content_type="qa", 
            min_tokens=500, 
            max_tokens=2000
        ),
        "summary": calculate_max_tokens(
            transcript_length, 
            content_type="summary", 
            min_tokens=600, 
            max_tokens=3000
        )
    }


if __name__ == "__main__":
    # Test with different content lengths
    test_lengths = [
        3000,    # ~3 minute video
        10000,   # ~10 minute video
        30000,   # ~30 minute video
        60000,   # ~1 hour video
        120000   # ~2 hour video
    ]
    
    print("Token scaling examples:")
    print("------------------------")
    
    for length in test_lengths:
        minutes = length / 1000  # Very rough approximation
        print(f"\nTranscript length: {length} chars (approx. {minutes:.0f} minutes)")
        
        limits = get_token_limits_for_transcript(length)
        for operation, limit in limits.items():
            print(f"  {operation}: {limit} tokens")
