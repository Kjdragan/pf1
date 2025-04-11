"""
Metadata extraction for Tavily Results Cleaner.

This module provides functions for extracting additional metadata
from content, such as publication date, author, and content type.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime


def extract_metadata(content: str, url: str, existing_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract additional metadata from content.
    
    Args:
        content: The content to analyze
        url: The URL of the content
        existing_metadata: Optional existing metadata to enhance
        
    Returns:
        A dictionary containing extracted metadata
    """
    # Initialize with existing metadata or empty dict
    metadata = existing_metadata or {}
    
    # Extract publication date if not already present
    if 'date' not in metadata or not metadata['date']:
        metadata['date'] = extract_date(content)
    
    # Extract author if not already present
    if 'author' not in metadata or not metadata['author']:
        metadata['author'] = extract_author(content)
    
    # Determine content type
    metadata['content_type'] = determine_content_type(content, url)
    
    return metadata


def extract_date(content: str) -> Optional[str]:
    """
    Extract publication date from content.
    
    Args:
        content: The content to analyze
        
    Returns:
        ISO format date string if found, None otherwise
    """
    # Common date patterns
    date_patterns = [
        # ISO format: 2023-04-25
        r'(\d{4}-\d{1,2}-\d{1,2})',
        
        # US format: 04/25/2023
        r'(\d{1,2}/\d{1,2}/\d{4})',
        
        # Long format: April 25, 2023
        r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}',
        
        # UK format: 25/04/2023
        r'(\d{1,2}/\d{1,2}/\d{4})',
        
        # Date with time: 2023-04-25 14:30
        r'(\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2})'
    ]
    
    # Look for date patterns near keywords
    date_keywords = [
        'published', 'updated', 'posted', 'date', 'written', 'created'
    ]
    
    # First, try to find dates near keywords
    for keyword in date_keywords:
        # Look for keyword in lowercase content
        content_lower = content.lower()
        keyword_pos = content_lower.find(keyword)
        
        if keyword_pos >= 0:
            # Extract a window around the keyword
            window_start = max(0, keyword_pos - 30)
            window_end = min(len(content), keyword_pos + 50)
            window = content[window_start:window_end]
            
            # Try to find a date in this window
            for pattern in date_patterns:
                match = re.search(pattern, window)
                if match:
                    date_str = match.group(0)
                    try:
                        # Try to parse and standardize the date
                        return standardize_date(date_str)
                    except:
                        pass
    
    # If no date found near keywords, look for any date in the first 1000 chars
    first_chunk = content[:1000]
    for pattern in date_patterns:
        match = re.search(pattern, first_chunk)
        if match:
            date_str = match.group(0)
            try:
                return standardize_date(date_str)
            except:
                pass
    
    return None


def extract_author(content: str) -> Optional[str]:
    """
    Extract author information from content.
    
    Args:
        content: The content to analyze
        
    Returns:
        Author name if found, None otherwise
    """
    # Common author patterns
    author_patterns = [
        # By Author Name
        r'[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
        
        # Author: Author Name
        r'[Aa]uthor:?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
        
        # Written by Author Name
        r'[Ww]ritten\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})',
        
        # Reporter: Author Name
        r'[Rr]eporter:?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})'
    ]
    
    # Try each pattern
    for pattern in author_patterns:
        match = re.search(pattern, content)
        if match:
            author = match.group(1).strip()
            # Validate author (should be 2-4 words, each capitalized)
            words = author.split()
            if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words):
                return author
    
    return None


def determine_content_type(content: str, url: str) -> str:
    """
    Determine the type of content.
    
    Args:
        content: The content to analyze
        url: The URL of the content
        
    Returns:
        Content type string
    """
    # Check URL for clues
    url_lower = url.lower()
    
    if any(term in url_lower for term in ['news', 'article', 'story']):
        return 'news_article'
    
    if any(term in url_lower for term in ['blog', 'opinion', 'column']):
        return 'blog_post'
    
    if any(term in url_lower for term in ['press-release', 'pressrelease', 'press/release']):
        return 'press_release'
    
    # Check content for clues
    content_lower = content.lower()
    
    # Count paragraphs
    paragraphs = re.split(r'\n\s*\n', content)
    paragraph_count = len(paragraphs)
    
    # Check for news article indicators
    news_indicators = ['reported', 'according to', 'sources said', 'officials', 'statement']
    news_count = sum(1 for indicator in news_indicators if indicator in content_lower)
    
    # Check for blog post indicators
    blog_indicators = ['i think', 'in my opinion', 'i believe', 'personally', 'my experience']
    blog_count = sum(1 for indicator in blog_indicators if indicator in content_lower)
    
    # Make determination based on indicators
    if news_count > blog_count:
        return 'news_article'
    elif blog_count > news_count:
        return 'blog_post'
    elif paragraph_count >= 5:
        return 'news_article'  # Default for longer content
    else:
        return 'short_content'


def standardize_date(date_str: str) -> str:
    """
    Standardize a date string to ISO format (YYYY-MM-DD).
    
    Args:
        date_str: The date string to standardize
        
    Returns:
        ISO format date string
        
    Raises:
        ValueError: If the date cannot be parsed
    """
    # Try different date formats
    formats = [
        '%Y-%m-%d',  # 2023-04-25
        '%m/%d/%Y',  # 04/25/2023
        '%d/%m/%Y',  # 25/04/2023
        '%B %d, %Y',  # April 25, 2023
        '%b %d, %Y',  # Apr 25, 2023
        '%B %d %Y',   # April 25 2023
        '%b %d %Y',   # Apr 25 2023
        '%Y-%m-%d %H:%M',  # 2023-04-25 14:30
        '%Y/%m/%d'    # 2023/04/25
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # If we get here, none of the formats matched
    raise ValueError(f"Could not parse date: {date_str}")
