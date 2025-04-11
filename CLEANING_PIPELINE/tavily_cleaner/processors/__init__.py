"""
Content post-processing utilities for Tavily search results.

This package contains processors for handling content truncation,
article boundary detection, and metadata extraction.
"""

from .truncator import truncate_content
from .boundary import detect_article_boundaries
from .metadata import extract_metadata

__all__ = [
    "truncate_content",
    "detect_article_boundaries",
    "extract_metadata"
]
