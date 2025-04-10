"""
Content Integration Node for YouTube Video Summarizer.
Transforms individual topic outputs into a cohesive document.
"""
import sys
import os
from typing import Dict, List, Any

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.integrate_content import integrate_content
from src.utils.logger import logger

class ContentIntegrationNode(BaseNode):
    """
    Node for transforming individual topic outputs into a cohesive document.
    """
    
    def __init__(self, shared_memory=None):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary
        """
        super().__init__(shared_memory)
        logger.debug("ContentIntegrationNode initialized")
    
    def prep(self):
        """
        Prepare for execution by checking if transformed_content, topics, and selected_rubric exist in shared memory.
        """
        required_keys = ["transformed_content", "topics", "selected_rubric"]
        missing_keys = [key for key in required_keys if key not in self.shared_memory]
        
        if missing_keys:
            error_msg = f"Missing required data in shared memory: {', '.join(missing_keys)}"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        if "error" in self.shared_memory:
            logger.warning(f"Skipping Content Integration due to previous error: {self.shared_memory['error']}")
            return
        
        # Validate transformed_content has entries for all topics
        topics = self.shared_memory["topics"]
        transformed_content = self.shared_memory["transformed_content"]
        missing_topics = [topic for topic in topics if topic not in transformed_content]
        
        if missing_topics:
            logger.warning(f"Some topics have no transformed content: {', '.join(missing_topics)}")
        
        logger.info(f"Preparing to integrate content for {len(topics)} topics")
    
    def exec(self):
        """
        Execute content integration using the data in shared memory.
        """
        if "error" in self.shared_memory:
            return
        
        topics = self.shared_memory["topics"]
        transformed_content = self.shared_memory["transformed_content"]
        selected_rubric = self.shared_memory["selected_rubric"]
        qa_pairs = self.shared_memory.get("qa_pairs", {})
        knowledge_level = self.shared_memory.get("knowledge_level", 5)
        
        logger.info("Starting content integration")
        
        try:
            # Integrate the content
            integrated_content = integrate_content(
                transformed_content=transformed_content,
                topics=topics,
                selected_rubric=selected_rubric,
                qa_pairs=qa_pairs,
                knowledge_level=knowledge_level
            )
            
            # Store the integrated content in shared memory
            self.shared_memory["integrated_content"] = integrated_content
            logger.info(f"Successfully integrated content ({len(integrated_content)} characters)")
            
            # Ensure Q&A pairs are preserved
            if "whole_content" in qa_pairs and qa_pairs["whole_content"]:
                logger.info(f"Preserving {len(qa_pairs['whole_content'])} Q&A pairs")
                # Make sure the Q&A pairs are properly copied to shared memory
                self.shared_memory["qa_pairs"] = qa_pairs
                self.shared_memory["qa_pairs"]["whole_content"] = qa_pairs["whole_content"]
                logger.info(f"Successfully stored {len(qa_pairs['whole_content'])} Q&A pairs in shared memory")
            else:
                logger.warning("No whole content Q&A pairs found")
                
        except Exception as e:
            error_msg = f"Failed to integrate content: {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
    
    def post(self):
        """
        Post-process after content integration.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Content Integration Node: {self.shared_memory['error']}")
            return
        
        if "integrated_content" in self.shared_memory:
            logger.info("Content Integration Node completed successfully")
        else:
            logger.warning("Content integration did not produce any output")


if __name__ == "__main__":
    # Test with sample data
    test_data = {
        "topics": ["Legal Background", "Court Ruling", "Implications"],
        "transformed_content": {
            "Legal Background": "In this episode of the Legal Breakdown, we examine a noteworthy development in the legal contest involving Donald Trump and the standing of states in legal challenges. Initially, a federal trial court ruled unfavorably against Trump's administration, declaring the termination of probationary employees unlawful and issuing a preliminary injunction to reinstate these individuals.",
            "Court Ruling": "The Fourth Circuit Court of Appeals has now overturned this injunction in a 2-1 decision. What is particularly intriguing here is that the appeals court refrained from making a determination regarding the legality of the terminations executed by the Trump administration.",
            "Implications": "This decision represents a provisional victory for the Trump administration and a setback for the employees, who were in the midst of being reinstated. The situation remains dynamic, but as it currently stands, the appeals court decision is a pivotal juncture, underscoring the intricate nature of legal standings in state-involved challenges."
        },
        "selected_rubric": {
            "name": "Analytical Narrative Transformation",
            "description": "Adds analytical commentary clearly separate from original ideas"
        }
    }
    
    # Create and run the node
    node = ContentIntegrationNode(test_data)
    updated_memory = node.run()
    
    # Print the results
    if "error" not in updated_memory:
        print("\nIntegrated Content:")
        print(updated_memory.get("integrated_content", "No integrated content found"))
    else:
        print(f"Error: {updated_memory['error']}")
