"""
Content truncation utilities for Tavily Results Cleaner.

This module provides functions for truncating content to a reasonable length
while preserving the most important information.
"""

import re
from typing import Dict, Any, Tuple


def truncate_content(content: str, max_chars: int = 10000, max_tokens: int = 5000) -> Dict[str, Any]:
    """
    Truncate content to a reasonable length while preserving important information.
    
    Args:
        content: The content to truncate
        max_chars: Maximum number of characters to keep
        max_tokens: Approximate maximum number of tokens to keep
        
    Returns:
        A dictionary containing:
            - 'content': The truncated content
            - 'truncated': Boolean indicating if truncation was performed
            - 'original_length': Length of the original content
            - 'truncated_length': Length of the truncated content
            - 'estimated_tokens': Estimated number of tokens in the truncated content
    """
    original_length = len(content)
    
    # If content is already within limits, return as is
    if original_length <= max_chars and estimate_tokens(content) <= max_tokens:
        return {
            'content': content,
            'truncated': False,
            'original_length': original_length,
            'truncated_length': original_length,
            'estimated_tokens': estimate_tokens(content)
        }
    
    # First try to truncate by paragraphs
    paragraphs = re.split(r'\n\s*\n', content)
    
    # If we have multiple paragraphs, try to keep as many as possible
    if len(paragraphs) > 1:
        truncated_content, is_truncated = _truncate_by_paragraphs(
            paragraphs, max_chars, max_tokens
        )
    else:
        # If we only have one paragraph, truncate by sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        truncated_content, is_truncated = _truncate_by_sentences(
            sentences, max_chars, max_tokens
        )
    
    truncated_length = len(truncated_content)
    estimated_tokens = estimate_tokens(truncated_content)
    
    return {
        'content': truncated_content,
        'truncated': is_truncated,
        'original_length': original_length,
        'truncated_length': truncated_length,
        'estimated_tokens': estimated_tokens
    }


def _truncate_by_paragraphs(paragraphs: list, max_chars: int, max_tokens: int) -> Tuple[str, bool]:
    """
    Truncate content by keeping as many paragraphs as possible within limits.
    
    Args:
        paragraphs: List of paragraphs
        max_chars: Maximum number of characters to keep
        max_tokens: Approximate maximum number of tokens to keep
        
    Returns:
        Tuple of (truncated_content, is_truncated)
    """
    result = []
    current_length = 0
    current_tokens = 0
    
    for paragraph in paragraphs:
        para_length = len(paragraph)
        para_tokens = estimate_tokens(paragraph)
        
        # If adding this paragraph would exceed limits, stop
        if current_length + para_length > max_chars or current_tokens + para_tokens > max_tokens:
            break
        
        result.append(paragraph)
        current_length += para_length + 2  # +2 for the newlines
        current_tokens += para_tokens
    
    # If we kept all paragraphs, no truncation was performed
    is_truncated = len(result) < len(paragraphs)
    
    # Join the paragraphs with double newlines
    truncated_content = '\n\n'.join(result)
    
    # If we truncated, add an indicator
    if is_truncated:
        truncated_content += '\n\n[Content truncated due to length]'
    
    return truncated_content, is_truncated


def _truncate_by_sentences(sentences: list, max_chars: int, max_tokens: int) -> Tuple[str, bool]:
    """
    Truncate content by keeping as many sentences as possible within limits.
    
    Args:
        sentences: List of sentences
        max_chars: Maximum number of characters to keep
        max_tokens: Approximate maximum number of tokens to keep
        
    Returns:
        Tuple of (truncated_content, is_truncated)
    """
    result = []
    current_length = 0
    current_tokens = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        sentence_tokens = estimate_tokens(sentence)
        
        # If adding this sentence would exceed limits, stop
        if current_length + sentence_length > max_chars or current_tokens + sentence_tokens > max_tokens:
            break
        
        result.append(sentence)
        current_length += sentence_length + 1  # +1 for the space
        current_tokens += sentence_tokens
    
    # If we kept all sentences, no truncation was performed
    is_truncated = len(result) < len(sentences)
    
    # Join the sentences with spaces
    truncated_content = ' '.join(result)
    
    # If we truncated, add an indicator
    if is_truncated:
        truncated_content += ' [Content truncated due to length]'
    
    return truncated_content, is_truncated


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    
    This is a simple approximation based on splitting by spaces and punctuation.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    
    # Split on spaces and punctuation
    tokens = re.findall(r'\w+|[^\w\s]', text)
    return len(tokens)
