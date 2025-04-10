"""
Utility to calculate LLM API costs and potential savings from optimizations like prompt caching.

This module provides functions to calculate the cost of API calls to the OpenAI API
and to estimate potential savings from prompt caching and other optimizations.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple

logger = logging.getLogger(__name__)

# OpenAI GPT-4o pricing per 1K tokens (as of April 2025)
# These rates may change over time and should be updated accordingly
GPT4O_INPUT_PRICE_PER_1K = 0.01  # $0.01 per 1K input tokens
GPT4O_OUTPUT_PRICE_PER_1K = 0.03  # $0.03 per 1K output tokens

class CostMetrics:
    """Class to track cost-related metrics for LLM API calls."""
    
    def __init__(self):
        """Initialize the metrics tracker."""
        self.total_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cached_tokens = 0
        self.calls_with_caching = 0
        self.estimated_cost = 0.0
        self.estimated_savings = 0.0
        
    def add_api_call(self, 
                    input_tokens: int, 
                    output_tokens: int, 
                    cached_tokens: int = 0,
                    model: str = "gpt-4o") -> None:
        """
        Add metrics from an API call.
        
        Args:
            input_tokens (int): Number of input tokens
            output_tokens (int): Number of output tokens
            cached_tokens (int): Number of cached input tokens (default: 0)
            model (str): The model used for the call (default: "gpt-4o")
        """
        self.total_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cached_tokens += cached_tokens
        
        if cached_tokens > 0:
            self.calls_with_caching += 1
        
        # Calculate costs
        input_cost = (input_tokens / 1000) * GPT4O_INPUT_PRICE_PER_1K
        output_cost = (output_tokens / 1000) * GPT4O_OUTPUT_PRICE_PER_1K
        cached_cost = (cached_tokens / 1000) * GPT4O_INPUT_PRICE_PER_1K * 0.5  # 50% discount
        
        # Calculate actual cost (considering caching discount)
        actual_cost = input_cost - cached_cost + output_cost
        self.estimated_cost += actual_cost
        
        # Calculate savings (what we would have paid without caching)
        full_cost = input_cost + output_cost
        call_savings = cached_cost  # This is the discount amount
        self.estimated_savings += call_savings
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of cost metrics and savings.
        
        Returns:
            Dict[str, Any]: Dictionary with cost metrics and savings
        """
        cache_hit_rate = 0
        if self.total_input_tokens > 0:
            cache_hit_rate = (self.total_cached_tokens / self.total_input_tokens) * 100
        
        return {
            "total_api_calls": self.total_calls,
            "calls_with_caching": self.calls_with_caching,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "cache_hit_rate_pct": round(cache_hit_rate, 2),
            "estimated_cost_usd": round(self.estimated_cost, 4),
            "estimated_savings_usd": round(self.estimated_savings, 4),
            "savings_percentage": round((self.estimated_savings / (self.estimated_cost + self.estimated_savings) * 100), 2) if self.estimated_cost + self.estimated_savings > 0 else 0
        }
    
    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.__init__()


def calculate_potential_savings(
    total_calls: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    cacheable_percentage: float = 0.7,
    avg_cache_hit_rate: float = 0.6
) -> Dict[str, Any]:
    """
    Calculate potential savings from implementing prompt caching.
    
    Args:
        total_calls (int): Estimated total number of API calls
        avg_input_tokens (int): Average input tokens per call
        avg_output_tokens (int): Average output tokens per call
        cacheable_percentage (float): Percentage of calls that could use caching (0.0-1.0)
        avg_cache_hit_rate (float): Average cache hit rate for cacheable calls (0.0-1.0)
        
    Returns:
        Dict[str, Any]: Dictionary with potential savings metrics
    """
    # Calculate baseline costs (without caching)
    total_input_tokens = total_calls * avg_input_tokens
    total_output_tokens = total_calls * avg_output_tokens
    
    input_cost = (total_input_tokens / 1000) * GPT4O_INPUT_PRICE_PER_1K
    output_cost = (total_output_tokens / 1000) * GPT4O_OUTPUT_PRICE_PER_1K
    baseline_cost = input_cost + output_cost
    
    # Calculate cacheable tokens
    cacheable_calls = total_calls * cacheable_percentage
    cacheable_tokens = cacheable_calls * avg_input_tokens
    
    # Calculate cached tokens (based on hit rate)
    cached_tokens = cacheable_tokens * avg_cache_hit_rate
    
    # Calculate cached cost (50% discount)
    cached_cost = (cached_tokens / 1000) * GPT4O_INPUT_PRICE_PER_1K * 0.5
    
    # Calculate optimized cost
    optimized_cost = baseline_cost - cached_cost
    
    return {
        "baseline_cost_usd": round(baseline_cost, 2),
        "optimized_cost_usd": round(optimized_cost, 2),
        "potential_savings_usd": round(cached_cost, 2),
        "savings_percentage": round((cached_cost / baseline_cost) * 100, 2),
        "estimated_cached_tokens": int(cached_tokens),
        "cacheable_calls": int(cacheable_calls),
        "avg_monthly_savings_usd": round(cached_cost * 30, 2)  # Assuming daily averages
    }


def generate_cost_report(metrics: CostMetrics) -> str:
    """
    Generate a formatted cost report based on metrics.
    
    Args:
        metrics (CostMetrics): The cost metrics object
        
    Returns:
        str: Formatted report as markdown
    """
    summary = metrics.get_summary()
    
    report = f"""
# LLM API Cost Report

## Usage Metrics
- Total API calls: {summary['total_api_calls']}
- Calls with caching: {summary['calls_with_caching']} ({summary['calls_with_caching']/summary['total_api_calls']*100:.1f}% of total)
- Total input tokens: {summary['total_input_tokens']:,}
- Total output tokens: {summary['total_output_tokens']:,}
- Total cached tokens: {summary['total_cached_tokens']:,}
- Cache hit rate: {summary['cache_hit_rate_pct']}%

## Cost Analysis
- Estimated cost: ${summary['estimated_cost_usd']}
- Estimated savings: ${summary['estimated_savings_usd']}
- Savings percentage: {summary['savings_percentage']}%
"""
    
    return report


# Global metrics instance for tracking costs across the application
global_metrics = CostMetrics()


if __name__ == "__main__":
    # Example usage
    metrics = CostMetrics()
    
    # Add some example API calls
    # Regular call without caching
    metrics.add_api_call(input_tokens=1500, output_tokens=500)
    
    # Call with caching (1000 tokens cached out of 2000)
    metrics.add_api_call(input_tokens=2000, output_tokens=700, cached_tokens=1000)
    
    # Generate and print a report
    print(generate_cost_report(metrics))
    
    # Example of potential savings calculation
    potential = calculate_potential_savings(
        total_calls=1000,
        avg_input_tokens=2000,
        avg_output_tokens=500,
        cacheable_percentage=0.8,
        avg_cache_hit_rate=0.7
    )
    
    print("\nPotential Savings Projection:")
    print(f"- Baseline cost: ${potential['baseline_cost_usd']}")
    print(f"- Optimized cost: ${potential['optimized_cost_usd']}")
    print(f"- Potential savings: ${potential['potential_savings_usd']} ({potential['savings_percentage']}%)")
    print(f"- Estimated monthly savings: ${potential['avg_monthly_savings_usd']}")
