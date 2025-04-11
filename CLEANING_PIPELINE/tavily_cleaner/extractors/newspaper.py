"""
Newspaper3k-based content extractor.

This module provides an implementation of the BaseExtractor interface
using the newspaper3k library for content extraction.
"""

import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import newspaper
from newspaper import Article

from .base import BaseExtractor


class NewspaperExtractor(BaseExtractor):
    """Content extractor using the newspaper3k library."""
    
    def __init__(self):
        """Initialize the newspaper extractor."""
        self._name = "newspaper3k"
        
    @property
    def name(self) -> str:
        """Get the name of this extractor."""
        return self._name
    
    def can_handle(self, url: str, html_content: Optional[str] = None) -> bool:
        """
        Check if this extractor can handle the given URL/content.
        
        The newspaper extractor can handle most news articles and blog posts.
        It's our primary extractor, so we return True for most URLs except
        for a few known problematic domains.
        
        Args:
            url: The URL of the content
            html_content: Optional HTML content for more detailed checking
            
        Returns:
            True if this extractor can handle the content, False otherwise
        """
        # Parse the URL to get the domain
        try:
            domain = urlparse(url).netloc.lower()
        except:
            return True  # If we can't parse the URL, we'll try anyway
        
        # List of domains that newspaper3k is known to have issues with
        problematic_domains = [
            'twitter.com', 'x.com',  # Social media
            'youtube.com', 'vimeo.com',  # Video platforms
            'github.com',  # Code repositories
            'docs.google.com',  # Google Docs
        ]
        
        # Check if the domain is in the problematic list
        for bad_domain in problematic_domains:
            if bad_domain in domain:
                return False
                
        return True
    
    def extract(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract clean content from HTML using newspaper3k.
        
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
            # Create an Article object
            article = Article(url)
            
            # Set the HTML content
            article.set_html(html_content)
            
            # Parse the article
            article.parse()
            
            # Extract the content
            result['content'] = article.text
            result['title'] = article.title
            
            # Extract metadata
            if article.authors:
                result['author'] = ', '.join(article.authors)
            
            if article.publish_date:
                result['date'] = article.publish_date.isoformat()
            
            # Mark as successful if we have content
            result['success'] = bool(result['content'])
            
        except Exception as e:
            result['error'] = str(e)
        
        # Add processing time
        result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        
        return result
