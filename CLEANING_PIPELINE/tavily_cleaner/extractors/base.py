"""
Base extractor interface for Tavily Results Cleaner.

This module defines the base interface for content extractors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseExtractor(ABC):
    """Base interface for content extractors."""
    
    @abstractmethod
    def extract(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract clean content from HTML.
        
        Args:
            html_content: The raw HTML content to extract from
            url: The URL of the content, used for context
            
        Returns:
            A dictionary containing:
                - 'content': The extracted clean text
                - 'title': The extracted title (if available)
                - 'author': The extracted author (if available)
                - 'date': The extracted publication date (if available)
                - 'success': Boolean indicating if extraction was successful
        """
        pass
    
    @abstractmethod
    def can_handle(self, url: str, html_content: Optional[str] = None) -> bool:
        """
        Check if this extractor can handle the given URL/content.
        
        Args:
            url: The URL of the content
            html_content: Optional HTML content for more detailed checking
            
        Returns:
            True if this extractor can handle the content, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this extractor."""
        pass
