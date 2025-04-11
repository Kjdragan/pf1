"""
Article boundary detection for Tavily Results Cleaner.

This module provides functions for detecting boundaries between articles
in content from aggregator sites.
"""

import re
from typing import Dict, Any, List, Tuple


def detect_article_boundaries(content: str) -> Dict[str, Any]:
    """
    Detect boundaries between articles in content from aggregator sites.
    
    Args:
        content: The content to analyze
        
    Returns:
        A dictionary containing:
            - 'articles': List of detected articles
            - 'is_aggregator': Boolean indicating if the content appears to be from an aggregator
            - 'main_article': The main/first article
            - 'article_count': Number of articles detected
    """
    # Check if this looks like an aggregator site
    is_aggregator = _is_likely_aggregator(content)
    
    if not is_aggregator:
        # If it's not an aggregator, treat the whole content as one article
        return {
            'articles': [content],
            'is_aggregator': False,
            'main_article': content,
            'article_count': 1
        }
    
    # Try to split content into articles
    articles = _split_into_articles(content)
    
    # If we couldn't split it, treat the whole content as one article
    if len(articles) <= 1:
        return {
            'articles': [content],
            'is_aggregator': False,
            'main_article': content,
            'article_count': 1
        }
    
    # Get the main article (usually the first one)
    main_article = articles[0]
    
    return {
        'articles': articles,
        'is_aggregator': True,
        'main_article': main_article,
        'article_count': len(articles)
    }


def _is_likely_aggregator(content: str) -> bool:
    """
    Check if the content is likely from an aggregator site.
    
    Args:
        content: The content to analyze
        
    Returns:
        True if the content appears to be from an aggregator site
    """
    # Check for patterns common in aggregator sites
    aggregator_patterns = [
        # Multiple headlines
        r'(?:\n|\r\n)#+\s+[A-Z]',
        # Multiple timestamps in different formats
        r'(?:\d{1,2}:\d{2}\s*(?:AM|PM|am|pm).*?){3,}',
        r'(?:\d{1,2}/\d{1,2}/\d{2,4}.*?){3,}',
        # "Read more" or "Full story" links
        r'(?:Read more|Full story|Continue reading).*?(?:Read more|Full story|Continue reading)',
        # Lists of news items
        r'(?:\n|\r\n)[-•*]\s+[A-Z].*?(?:\n|\r\n)[-•*]\s+[A-Z]',
        # Multiple bylines
        r'(?:By\s+[A-Z][a-z]+\s+[A-Z][a-z]+).*?(?:By\s+[A-Z][a-z]+\s+[A-Z][a-z]+)'
    ]
    
    for pattern in aggregator_patterns:
        if re.search(pattern, content):
            return True
    
    # Check for multiple date patterns
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',
        r'\d{1,2}-\d{1,2}-\d{2,4}',
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}'
    ]
    
    date_counts = 0
    for pattern in date_patterns:
        matches = re.findall(pattern, content)
        date_counts += len(matches)
    
    # If we find multiple dates, it's likely an aggregator
    if date_counts >= 3:
        return True
    
    return False


def _split_into_articles(content: str) -> List[str]:
    """
    Split content into separate articles.
    
    Args:
        content: The content to split
        
    Returns:
        List of articles
    """
    # Try different splitting strategies
    strategies = [
        _split_by_headlines,
        _split_by_hr,
        _split_by_large_gaps,
        _split_by_timestamps
    ]
    
    for strategy in strategies:
        articles = strategy(content)
        if len(articles) > 1:
            return articles
    
    # If no strategy worked, return the whole content as one article
    return [content]


def _split_by_headlines(content: str) -> List[str]:
    """
    Split content by headline patterns.
    
    Args:
        content: The content to split
        
    Returns:
        List of articles
    """
    # Look for headline patterns like "# Headline" or "HEADLINE:"
    headline_patterns = [
        r'\n#+\s+[A-Z]',  # Markdown-style headlines
        r'\n[A-Z][A-Z\s]+:',  # ALL CAPS headlines with colon
        r'\n\d+\.\s+[A-Z]'  # Numbered headlines
    ]
    
    splits = []
    for pattern in headline_patterns:
        matches = list(re.finditer(pattern, content))
        if len(matches) >= 2:  # Need at least 2 matches to split
            splits.extend([m.start() for m in matches])
    
    if not splits:
        return [content]
    
    # Sort the split positions
    splits.sort()
    
    # Split the content
    articles = []
    for i in range(len(splits)):
        start = splits[i]
        end = splits[i+1] if i < len(splits) - 1 else len(content)
        article = content[start:end].strip()
        if article:
            articles.append(article)
    
    # Add the content before the first split if it exists
    if splits[0] > 0:
        first_part = content[:splits[0]].strip()
        if first_part:
            articles.insert(0, first_part)
    
    return articles


def _split_by_hr(content: str) -> List[str]:
    """
    Split content by horizontal rule patterns.
    
    Args:
        content: The content to split
        
    Returns:
        List of articles
    """
    # Look for horizontal rule patterns
    hr_patterns = [
        r'\n-{3,}\n',
        r'\n\*{3,}\n',
        r'\n_{3,}\n'
    ]
    
    for pattern in hr_patterns:
        parts = re.split(pattern, content)
        if len(parts) > 1:
            return [part.strip() for part in parts if part.strip()]
    
    return [content]


def _split_by_large_gaps(content: str) -> List[str]:
    """
    Split content by large gaps between paragraphs.
    
    Args:
        content: The content to split
        
    Returns:
        List of articles
    """
    # Look for large gaps (multiple blank lines)
    parts = re.split(r'\n\s*\n\s*\n\s*\n', content)
    if len(parts) > 1:
        return [part.strip() for part in parts if part.strip()]
    
    return [content]


def _split_by_timestamps(content: str) -> List[str]:
    """
    Split content by timestamp patterns.
    
    Args:
        content: The content to split
        
    Returns:
        List of articles
    """
    # Look for timestamp patterns
    timestamp_patterns = [
        r'\n\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)',
        r'\n\d{1,2}/\d{1,2}/\d{2,4}',
        r'\n(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}'
    ]
    
    splits = []
    for pattern in timestamp_patterns:
        matches = list(re.finditer(pattern, content))
        if len(matches) >= 2:  # Need at least 2 matches to split
            splits.extend([m.start() for m in matches])
    
    if not splits:
        return [content]
    
    # Sort the split positions
    splits.sort()
    
    # Split the content
    articles = []
    for i in range(len(splits)):
        start = splits[i]
        end = splits[i+1] if i < len(splits) - 1 else len(content)
        article = content[start:end].strip()
        if article:
            articles.append(article)
    
    # Add the content before the first split if it exists
    if splits[0] > 0:
        first_part = content[:splits[0]].strip()
        if first_part:
            articles.insert(0, first_part)
    
    return articles
