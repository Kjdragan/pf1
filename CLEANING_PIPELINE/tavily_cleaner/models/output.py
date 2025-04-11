"""
Output models for Tavily Results Cleaner.

This module provides data classes for representing cleaned Tavily search results.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import datetime


@dataclass
class ExtractionMetadata:
    """Metadata about the extraction process for a single result item."""
    strategy: str  # The extraction strategy used (newspaper, trafilatura, fallback)
    truncated: bool = False  # Whether the content was truncated
    original_length: int = 0  # Original length of the raw content
    cleaned_length: int = 0  # Length of the cleaned content
    processing_time_ms: int = 0  # Time taken to process this item
    publication_date: Optional[str] = None  # Extracted publication date if available
    author: Optional[str] = None  # Extracted author if available
    content_type: str = "unknown"  # Type of content (news_article, blog_post, etc.)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "strategy": self.strategy,
            "truncated": self.truncated,
            "original_length": self.original_length,
            "cleaned_length": self.cleaned_length,
            "processing_time_ms": self.processing_time_ms,
            "publication_date": self.publication_date,
            "author": self.author,
            "content_type": self.content_type
        }


@dataclass
class CleanedTavilyResult:
    """Represents a cleaned Tavily search result item."""
    # Original fields from Tavily
    title: str
    url: str
    content: str  # Original content snippet
    score: float
    
    # Added fields
    cleaned_content: str  # The cleaned and processed content
    extraction_metadata: ExtractionMetadata
    
    # Optional original raw content
    raw_content: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score,
            "cleaned_content": self.cleaned_content,
            "extraction_metadata": self.extraction_metadata.to_dict()
        }
        
        # Only include raw_content if it exists
        if self.raw_content:
            result["raw_content"] = self.raw_content
            
        return result


@dataclass
class CleanedTavilyResults:
    """Represents the complete cleaned Tavily search results."""
    query: str
    results: List[CleanedTavilyResult]
    processing_metadata: Dict[str, Any] = field(default_factory=lambda: {
        "processed_at": datetime.datetime.now().isoformat(),
        "version": "1.0.0"
    })
    
    # Optional fields that might be in the original response
    answer: Optional[str] = None
    response_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "query": self.query,
            "results": [item.to_dict() for item in self.results],
            "processing_metadata": self.processing_metadata
        }
        
        # Include optional fields if they exist
        if self.answer:
            result["answer"] = self.answer
        if self.response_time is not None:
            result["response_time"] = self.response_time
            
        return result
