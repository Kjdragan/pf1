"""
Audience Wrapper Node for YouTube Video Summarizer.

This node applies audience sophistication wrapper to transformed content.
"""
import sys
import os

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.apply_audience_wrapper import apply_audience_wrapper
from src.utils.logger import logger

class AudienceWrapperNode(BaseNode):
    """
    Node that applies audience sophistication wrapper to transformed content.
    
    This node:
    1. Reads transformed content and audience level from shared memory
    2. Applies audience wrapper to adjust content to target sophistication level
    3. Updates transformed content in shared memory
    """
    
    def __init__(self, shared_memory=None):
        """Initialize the AudienceWrapperNode."""
        super().__init__(shared_memory)
        logger.info("AudienceWrapperNode initialized")
    
    def prep(self):
        """
        Prepare for execution by reading necessary data from shared memory.
        
        Reads:
        - transformed_content: dict mapping topics to their transformed content
        - audience_level: str representing selected audience level
        """
        logger.info("Reading transformed content and audience level from shared memory")
        
        # Check if required data exists in shared memory
        if "transformed_content" not in self.shared_memory or not self.shared_memory["transformed_content"]:
            error_msg = "Transformed content not found in shared memory or content is empty"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        if "audience_level" not in self.shared_memory:
            error_msg = "Audience level not found in shared memory"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        self.transformed_content = self.shared_memory["transformed_content"]
        self.audience_level = self.shared_memory["audience_level"]
        
        logger.debug(f"Found {len(self.transformed_content)} topics with transformed content")
        logger.debug(f"Using audience level: {self.audience_level}")
    
    def exec(self):
        """
        Execute the node's main functionality.
        
        Applies audience wrapper to adjust content to target sophistication level.
        """
        if "error" in self.shared_memory:
            return
            
        logger.info(f"Applying {self.audience_level} audience wrapper to content")
        
        try:
            # Call apply_audience_wrapper utility
            self.adjusted_content = apply_audience_wrapper(
                self.transformed_content, 
                self.audience_level
            )
            
            logger.info(f"Successfully applied audience wrapper to {len(self.adjusted_content)} topics")
            
        except Exception as e:
            error_msg = f"Error applying audience wrapper: {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
    
    def post(self):
        """
        Post-process and write results to shared memory.
        
        Updates:
        - transformed_content: dict with audience-adjusted content
        """
        if "error" in self.shared_memory:
            return
            
        logger.info("Updating transformed content in shared memory with audience-adjusted content")
        
        # Replace the transformed content with audience-adjusted content
        self.shared_memory["transformed_content"] = self.adjusted_content
        
        # Log completion
        logger.info("Audience wrapper application completed")


if __name__ == "__main__":
    # Test with sample transformed content
    test_transformed_content = {
        "Machine Learning Basics": """
## Machine Learning Basics

Machine learning is a subset of artificial intelligence that focuses on building systems 
that learn from data. Unlike traditional programming where you explicitly program rules, 
in machine learning, you train models on data and they learn patterns.

Key aspects include:
- Supervised learning: Training on labeled data
- Unsupervised learning: Finding patterns in unlabeled data
- Reinforcement learning: Learning through reward-based feedback
""",
        "Deep Learning": """
## Deep Learning

Deep learning is a specialized form of machine learning using neural networks with many layers.
These architectures enable automatic feature extraction from raw data, allowing models to
learn complex patterns with minimal human intervention.

Applications include:
- Image and speech recognition
- Natural language processing
- Autonomous vehicles
"""
    }
    
    # Initialize shared memory
    shared_memory = {
        "transformed_content": test_transformed_content,
        "audience_level": "general"
    }
    
    # Create and run the node
    node = AudienceWrapperNode(shared_memory)
    updated_memory = node.run()
    
    # Print the results if no error
    if "error" not in updated_memory:
        print("\nAudience-Adjusted Content:")
        
        # Print transformed content
        adjusted_content = updated_memory.get("transformed_content", {})
        for topic, content in adjusted_content.items():
            print(f"\n## {topic}:")
            print(content)
    else:
        print(f"Error: {updated_memory['error']}")
