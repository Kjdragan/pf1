"""
Trafilatura-based content extractor.

This module provides an implementation of the BaseExtractor interface
using the trafilatura library for content extraction.
"""

import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Import trafilatura with error handling since it's an optional dependency
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

from .base import BaseExtractor


class TrafilaturaExtractor(BaseExtractor):
    """Content extractor using the trafilatura library."""
    
    def __init__(self):
        """Initialize the trafilatura extractor."""
        self._name = "trafilatura"
        if not TRAFILATURA_AVAILABLE:
            print("Warning: trafilatura library not available. Install with 'uv add trafilatura'")
    
    @property
    def name(self) -> str:
        """Get the name of this extractor."""
        return self._name
    
    def can_handle(self, url: str, html_content: Optional[str] = None) -> bool:
        """
        Check if this extractor can handle the given URL/content.
        
        Trafilatura works well as a fallback for most content types.
        
        Args:
            url: The URL of the content
            html_content: Optional HTML content for more detailed checking
            
        Returns:
            True if trafilatura is available, False otherwise
        """
        return TRAFILATURA_AVAILABLE
    
    def extract(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract clean content from HTML using trafilatura.
        
        Args:
            html_content: The raw HTML content to extract from
            url: The URL of the content, used for context
            
        Returns:
            A dictionary containing extracted content and metadata
        """
        start_time = time.time()
        result = {
            'content': '',
            'title': '',
            'author': None,
            'date': None,
            'success': False
        }
        
        if not TRAFILATURA_AVAILABLE:
            result['error'] = "Trafilatura library not available"
            return result
        
        try:
            # Extract the content using trafilatura
            extracted = trafilatura.extract(
                html_content,
                url=url,
                output_format='json',
                with_metadata=True,
                include_comments=False,
                include_tables=True,
                favor_precision=True,
                date_extraction_params={'extensive_search': True}
            )
            
            if extracted:
                # Convert from JSON string to dict
                import json
                data = json.loads(extracted)
                
                # Extract the content
                result['content'] = data.get('text', '')
                result['title'] = data.get('title', '')
                
                # Extract metadata
                result['author'] = data.get('author')
                result['date'] = data.get('date')
                
                # Mark as successful if we have content
                result['success'] = bool(result['content'])
            else:
                result['error'] = "Trafilatura extraction returned None"
        
        except Exception as e:
            result['error'] = str(e)
        
        # Add processing time
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        
        return result
