"""
Fallback content extractor using simple regex patterns.

This module provides a last-resort extractor when more sophisticated
methods like newspaper3k and trafilatura fail.
"""

import re
import time
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

from .base import BaseExtractor


class FallbackExtractor(BaseExtractor):
    """Simple fallback content extractor using BeautifulSoup and regex patterns."""
    
    def __init__(self):
        """Initialize the fallback extractor."""
        self._name = "fallback"
    
    @property
    def name(self) -> str:
        """Get the name of this extractor."""
        return self._name
    
    def can_handle(self, url: str, html_content: Optional[str] = None) -> bool:
        """
        Check if this extractor can handle the given URL/content.
        
        The fallback extractor can handle any content as a last resort.
        
        Args:
            url: The URL of the content
            html_content: Optional HTML content for more detailed checking
            
        Returns:
            Always returns True as this is a fallback extractor
        """
        return True
    
    def extract(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract clean content from HTML using simple regex patterns.
        
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
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script, style, and other non-content elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try to extract title
            title_tag = soup.find('title')
            if title_tag and title_tag.text:
                result['title'] = title_tag.text.strip()
            
            # Try to find main content containers
            main_content = None
            for container in ['main', 'article', '[role="main"]', '.main-content', '#main-content', '.article-body', '.content']:
                content_div = soup.select_one(container)
                if content_div:
                    main_content = content_div
                    break
            
            # If no main content container found, use the body
            if not main_content:
                main_content = soup.body
            
            # Extract paragraphs from main content
            if main_content:
                paragraphs = main_content.find_all('p')
                content = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
                result['content'] = content
            
            # Try to extract author
            author_candidates = [
                soup.select_one('.author'),
                soup.select_one('[rel="author"]'),
                soup.select_one('.byline')
            ]
            
            for candidate in author_candidates:
                if candidate and candidate.get_text().strip():
                    result['author'] = candidate.get_text().strip()
                    break
            
            # Try to extract date
            date_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
            date_matches = re.search(date_pattern, html_content)
            if date_matches:
                result['date'] = date_matches.group(1)
            
            # Mark as successful if we have content
            result['success'] = bool(result['content'])
            
        except Exception as e:
            result['error'] = str(e)
        
        # Add processing time
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        
        return result
