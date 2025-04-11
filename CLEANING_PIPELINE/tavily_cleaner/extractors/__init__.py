"""
Content extraction strategies for Tavily search results.

This package contains various extractors for processing raw HTML content
from Tavily search results into clean, structured text.
"""

from .factory import get_extractor
from .newspaper import NewspaperExtractor
from .trafilatura import TrafilaturaExtractor
from .fallback import FallbackExtractor

__all__ = [
    "get_extractor",
    "NewspaperExtractor", 
    "TrafilaturaExtractor",
    "FallbackExtractor"
]
