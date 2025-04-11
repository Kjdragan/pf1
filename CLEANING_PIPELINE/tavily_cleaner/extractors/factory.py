"""
Extractor factory for selecting the appropriate content extraction strategy.

This module provides a factory function for selecting the best extractor
based on the URL and content.
"""

from typing import Optional, List
from urllib.parse import urlparse

from .base import BaseExtractor
from .newspaper import NewspaperExtractor
from .trafilatura import TrafilaturaExtractor
from .fallback import FallbackExtractor


def get_extractor(url: str, html_content: Optional[str] = None) -> BaseExtractor:
    """
    Get the most appropriate extractor for the given URL and content.
    
    Args:
        url: The URL of the content
        html_content: Optional HTML content for more detailed checking
        
    Returns:
        An instance of the most appropriate BaseExtractor implementation
    """
    # Create all available extractors
    extractors: List[BaseExtractor] = [
        NewspaperExtractor(),
        TrafilaturaExtractor(),
        FallbackExtractor()
    ]
    
    # Try to determine the domain type for better extractor selection
    domain_type = _get_domain_type(url)
    
    # Select the appropriate extractor based on domain type and URL
    if domain_type == 'news':
        # For news sites, newspaper3k is usually the best choice
        for extractor in extractors:
            if extractor.name == 'newspaper3k' and extractor.can_handle(url, html_content):
                return extractor
    elif domain_type == 'social':
        # For social media, trafilatura often works better
        for extractor in extractors:
            if extractor.name == 'trafilatura' and extractor.can_handle(url, html_content):
                return extractor
    
    # For other cases or if the preferred extractor can't handle it,
    # try each extractor in order of preference
    for extractor in extractors:
        if extractor.can_handle(url, html_content):
            return extractor
    
    # If all else fails, return the fallback extractor
    return FallbackExtractor()


def _get_domain_type(url: str) -> str:
    """
    Determine the type of domain from the URL.
    
    Args:
        url: The URL to analyze
        
    Returns:
        A string indicating the domain type: 'news', 'social', or 'other'
    """
    try:
        domain = urlparse(url).netloc.lower()
    except:
        return 'other'
    
    # List of known news domains
    news_domains = [
        'nytimes.com', 'washingtonpost.com', 'cnn.com', 'bbc.com', 'bbc.co.uk',
        'reuters.com', 'apnews.com', 'npr.org', 'theguardian.com', 'wsj.com',
        'foxnews.com', 'nbcnews.com', 'abcnews.go.com', 'cbsnews.com',
        'aljazeera.com', 'bloomberg.com', 'economist.com', 'ft.com',
        'time.com', 'newsweek.com', 'politico.com', 'thehill.com',
        'usatoday.com', 'latimes.com', 'chicagotribune.com', 'nypost.com',
        'news.yahoo.com', 'news.google.com'
    ]
    
    # List of known social media domains
    social_domains = [
        'twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'linkedin.com',
        'reddit.com', 'tiktok.com', 'youtube.com', 'pinterest.com',
        'tumblr.com', 'quora.com', 'medium.com', 'threads.net'
    ]
    
    # Check if the domain matches any known type
    for news_domain in news_domains:
        if news_domain in domain:
            return 'news'
    
    for social_domain in social_domains:
        if social_domain in domain:
            return 'social'
    
    # Default to 'other' if no match
    return 'other'
