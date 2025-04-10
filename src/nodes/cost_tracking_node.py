"""
Cost Tracking Node for YouTube Video Summarizer.
Tracks and reports on LLM API costs and calculates savings from optimizations.
"""
import sys
import os
import json
import datetime

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.calculate_llm_costs import global_metrics, generate_cost_report, calculate_potential_savings
from src.utils.logger import logger

class CostTrackingNode(BaseNode):
    """
    Node for tracking LLM API costs and reporting on savings from optimizations.
    This node is designed to be used at the end of the flow to generate cost reports.
    """
    
    def __init__(self, shared_memory=None):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary
        """
        super().__init__(shared_memory or {})
        self.reset_metrics = self.shared_memory.get("reset_metrics", False)
        self.include_projections = self.shared_memory.get("include_projections", True)
        self.projection_days = self.shared_memory.get("projection_days", 30)
        
        logger.debug(f"CostTrackingNode initialized with reset_metrics={self.reset_metrics}")
    
    def prep(self):
        """
        Prepare for execution by checking prerequisites.
        """
        # No specific prerequisites needed for this node
        logger.info("Preparing to generate cost tracking report")
        
    def exec(self):
        """
        Generate a cost tracking report based on the global metrics.
        """
        try:
            # Generate the cost report
            logger.info("Generating cost tracking report")
            cost_report = generate_cost_report(global_metrics)
            
            # Store the report in shared memory
            self.shared_memory["cost_report"] = cost_report
            self.shared_memory["cost_metrics"] = global_metrics.get_summary()
            
            # Generate a filename for the report
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"cost_report_{timestamp}.md"
            self.shared_memory["cost_report_filename"] = report_filename
            
            # Save the report to a file
            report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports", report_filename)
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w') as f:
                f.write(cost_report)
            
            logger.info(f"Cost report saved to: {report_path}")
            
            # Reset the metrics if requested
            if self.reset_metrics:
                logger.info("Resetting cost metrics")
                global_metrics.reset()
                
        except Exception as e:
            error_msg = f"Error generating cost report: {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
    
    def post(self):
        """
        Post-process the cost tracking results.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Cost Tracking Node: {self.shared_memory['error']}")
            return
        
        # Add a summary to the logging output
        metrics = global_metrics.get_summary()
        logger.info(f"Cost Tracking Summary:")
        logger.info(f"- Total API calls: {metrics['total_api_calls']}")
        logger.info(f"- Calls with caching: {metrics['calls_with_caching']}")
        logger.info(f"- Total input tokens: {metrics['total_input_tokens']}")
        logger.info(f"- Total cached tokens: {metrics['total_cached_tokens']}")
        logger.info(f"- Estimated cost: ${metrics['estimated_cost_usd']}")
        logger.info(f"- Estimated savings: ${metrics['estimated_savings_usd']} ({metrics['savings_percentage']}%)")


if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Simulate some API calls in the global metrics
    from src.utils.calculate_llm_costs import global_metrics
    
    # Regular call without caching
    global_metrics.add_api_call(input_tokens=1500, output_tokens=500)
    
    # Call with caching (1000 tokens cached out of 2000)
    global_metrics.add_api_call(input_tokens=2000, output_tokens=700, cached_tokens=1000)
    
    # Create and run the node
    shared_memory = {
        "reset_metrics": False,
        "include_projections": True
    }
    
    node = CostTrackingNode(shared_memory)
    node.run()
    
    # Print the results
    if "error" not in shared_memory:
        print("\nCost Tracking Results:")
        print(f"Cost report generated successfully")
        print(f"Report file: {shared_memory.get('cost_report_filename')}")
        print("\nMetrics Summary:")
        metrics = shared_memory["cost_metrics"]
        print(f"- Total API calls: {metrics['total_api_calls']}")
        print(f"- Calls with caching: {metrics['calls_with_caching']}")
        print(f"- Cache hit rate: {metrics['cache_hit_rate_pct']}%")
        print(f"- Estimated cost: ${metrics['estimated_cost_usd']}")
        print(f"- Estimated savings: ${metrics['estimated_savings_usd']} ({metrics['savings_percentage']}%)")
    else:
        print(f"Error: {shared_memory['error']}")
