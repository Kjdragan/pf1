"""
Data models for Tavily Results Cleaner.

This package contains input validators and output formatters
for the Tavily Results Cleaner module.
"""

from .input import validate_tavily_results, TavilyResult
from .output import CleanedTavilyResult, ExtractionMetadata

__all__ = [
    "validate_tavily_results",
    "TavilyResult",
    "CleanedTavilyResult",
    "ExtractionMetadata"
]
