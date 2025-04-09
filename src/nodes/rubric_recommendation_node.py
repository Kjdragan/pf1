"""
Rubric Recommendation Node for YouTube Video Summarizer.

This node analyzes content and suggests appropriate transformation rubrics.
"""
import sys
import os

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.recommend_rubric import recommend_rubric
from src.utils.logger import logger

class RubricRecommendationNode(BaseNode):
    """
    Node that analyzes content and suggests appropriate transformation rubrics.
    
    This node:
    1. Reads transcript and topics from shared memory
    2. Uses recommend_rubric utility to analyze content
    3. Writes recommended rubrics to shared memory
    """
    
    def __init__(self, shared_memory=None):
        """Initialize the RubricRecommendationNode."""
        super().__init__(shared_memory)
        logger.info("RubricRecommendationNode initialized")
    
    def prep(self):
        """
        Prepare for execution by reading necessary data from shared memory.
        
        Reads:
        - transcript: str
        - topics: list
        """
        logger.info("Reading transcript and topics from shared memory")
        
        # Check if required data exists in shared memory
        if "transcript" not in self.shared_memory:
            error_msg = "Transcript not found in shared memory"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        if "topics" not in self.shared_memory or not self.shared_memory["topics"]:
            error_msg = "Topics not found in shared memory or topics list is empty"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        self.transcript = self.shared_memory["transcript"]
        self.topics = self.shared_memory["topics"]
        
        logger.debug(f"Found {len(self.topics)} topics for rubric recommendation")
    
    def exec(self):
        """
        Execute the node's main functionality.
        
        Calls recommend_rubric utility to analyze content and suggest appropriate rubrics.
        """
        logger.info("Analyzing content and recommending appropriate rubrics")
        
        try:
            # Call recommend_rubric to get recommendations
            self.recommended_rubrics = recommend_rubric(self.transcript, self.topics)
            
            logger.info(f"Successfully generated {len(self.recommended_rubrics)} rubric recommendations")
            top_recommendation = self.recommended_rubrics[0] if self.recommended_rubrics else None
            if top_recommendation:
                logger.info(f"Top recommendation: {top_recommendation['name']} with confidence {top_recommendation['confidence']}%")
                
        except Exception as e:
            error_msg = f"Error recommending rubrics: {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
    
    def post(self):
        """
        Post-process and write results to shared memory.
        
        Writes:
        - recommended_rubrics: list of dicts with rubric details
        """
        logger.info("Writing recommended rubrics to shared memory")
        
        # Write recommended rubrics to shared memory
        self.shared_memory["recommended_rubrics"] = self.recommended_rubrics
        
        # Log completion
        logger.info("Rubric recommendation completed")
