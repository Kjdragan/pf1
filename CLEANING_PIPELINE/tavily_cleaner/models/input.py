"""
Input validation and models for Tavily search results.

This module provides functions and classes for validating and
representing Tavily search results.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import json


@dataclass
class TavilyResult:
    """Represents a single result item from Tavily search."""
    title: str
    url: str
    content: str
    score: float
    raw_content: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TavilyResult':
        """Create a TavilyResult instance from a dictionary."""
        return cls(
            title=data.get('title', 'No title'),
            url=data.get('url', ''),
            content=data.get('content', ''),
            score=data.get('score', 0.0),
            raw_content=data.get('raw_content')
        )
    
    def has_raw_content(self) -> bool:
        """Check if this result has raw content available."""
        return self.raw_content is not None and len(self.raw_content) > 0


def validate_tavily_results(data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Validate that the input data is a valid Tavily search result.
    
    Args:
        data: Either a dictionary or a JSON string representing Tavily search results
        
    Returns:
        A dictionary representing the validated Tavily search results
        
    Raises:
        ValueError: If the data is not valid Tavily search results
    """
    # Convert string to dict if needed
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string provided")
    
    # Check that it's a dictionary
    if not isinstance(data, dict):
        raise ValueError("Tavily results must be a dictionary")
    
    # Check for required fields
    if 'query' not in data:
        raise ValueError("Missing 'query' field in Tavily results")
    
    if 'results' not in data:
        raise ValueError("Missing 'results' field in Tavily results")
    
    # Check that results is a list
    if not isinstance(data['results'], list):
        raise ValueError("'results' field must be a list")
    
    # Validate each result item
    for i, result in enumerate(data['results']):
        if not isinstance(result, dict):
            raise ValueError(f"Result item {i} must be a dictionary")
        
        # Check for required fields in each result
        for field in ['title', 'url', 'content', 'score']:
            if field not in result:
                raise ValueError(f"Missing '{field}' in result item {i}")
    
    return data
