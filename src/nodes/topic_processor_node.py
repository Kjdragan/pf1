"""
Topic Processor Node for YouTube Video Summarizer.
Processes a single topic with Q&A generation and rubric transformation.
"""
import sys
import os
import json

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.generate_qa import generate_qa_pairs
from src.utils.apply_rubric import apply_rubric
from src.utils.logger import logger

class TopicProcessorNode(BaseNode):
    """
    Node for processing a single topic, including Q&A generation and content transformation.
    This node is designed to be used as part of a Map-Reduce pattern.
    """
    
    def __init__(self, shared_memory=None, topic=None, transcript=None, selected_rubric=None, questions_per_topic=3):
        """
        Initialize the node with topic, transcript, and rubric information.
        
        Args:
            shared_memory (dict): Shared memory dictionary (optional)
            topic (str): The topic to process
            transcript (str): The video transcript
            selected_rubric (dict): The selected rubric information
            questions_per_topic (int): Number of questions to generate per topic
        """
        super().__init__(shared_memory or {})
        self.topic = topic
        self.transcript = transcript
        self.selected_rubric = selected_rubric
        self.questions_per_topic = questions_per_topic
        self.result = {
            "topic": topic,
            "qa_pairs": [],
            "transformed_content": ""
        }
        logger.debug(f"TopicProcessorNode initialized for topic: {topic}")
    
    def prep(self):
        """
        Prepare for execution by checking if topic, transcript, and rubric are available.
        """
        # If topic and transcript were not provided in constructor, try to get from shared memory
        if self.topic is None and "current_topic" in self.shared_memory:
            self.topic = self.shared_memory["current_topic"]
            
        if self.transcript is None and "transcript" in self.shared_memory:
            self.transcript = self.shared_memory["transcript"]
            
        if self.selected_rubric is None and "selected_rubric" in self.shared_memory:
            self.selected_rubric = self.shared_memory["selected_rubric"]
            
        if self.topic is None:
            error_msg = "No topic provided for processing"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        if self.transcript is None:
            error_msg = "No transcript provided for processing"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        if self.selected_rubric is None:
            error_msg = "No rubric provided for content transformation"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        logger.info(f"Processing topic: {self.topic} with rubric: {self.selected_rubric.get('name', 'Unknown')}")
    
    def exec(self):
        """
        Execute topic processing: generate Q&A pairs and apply transformation.
        """
        if "error" in self.shared_memory:
            return
            
        # Step 1: Generate Q&A pairs
        self._generate_qa_pairs()
        
        # Step 2: Apply selected rubric transformation
        self._apply_rubric_transformation()
    
    def _generate_qa_pairs(self):
        """
        Generate Q&A pairs for the topic using the generate_qa utility.
        """
        logger.info(f"Generating Q&A pairs for topic: {self.topic}")
        
        try:
            # Call the generate_qa_pairs utility
            qa_pairs = generate_qa_pairs(self.topic, self.transcript, self.questions_per_topic)
            
            # Store the Q&A pairs
            self.result["qa_pairs"] = qa_pairs
            logger.info(f"Generated {len(qa_pairs)} Q&A pairs for topic '{self.topic}'")
            
        except Exception as e:
            error_msg = f"Error generating Q&A pairs for topic '{self.topic}': {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
    
    def _apply_rubric_transformation(self):
        """
        Apply the selected rubric transformation to the topic's content.
        """
        if "error" in self.shared_memory or not self.result["qa_pairs"]:
            return
            
        logger.info(f"Applying {self.selected_rubric.get('rubric_id', 'unknown')} rubric to topic: {self.topic}")
        
        try:
            # Prepare content for rubric transformation
            topic_content = {
                "topics": [self.topic],
                "qa_pairs": {
                    self.topic: self.result["qa_pairs"]
                }
            }
            
            # Call the apply_rubric utility
            transformed_result = apply_rubric(
                topic_content, 
                self.selected_rubric.get("rubric_id", "insightful_conversational")
            )
            
            # Store the transformed content
            if transformed_result and "transformed_content" in transformed_result:
                self.result["transformed_content"] = transformed_result["transformed_content"].get(self.topic, "")
                logger.info(f"Successfully applied rubric transformation to topic '{self.topic}'")
            else:
                error_msg = f"Rubric transformation failed for topic '{self.topic}'"
                logger.error(error_msg)
                self.result["transformed_content"] = f"Transformation error for {self.topic}."
                
        except Exception as e:
            error_msg = f"Error applying rubric to topic '{self.topic}': {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
            self.result["transformed_content"] = f"Error transforming {self.topic}: {str(e)}"
    
    def post(self):
        """
        Post-process and return the results.
        """
        # Store the results in shared memory if needed
        if "topic_results" not in self.shared_memory:
            self.shared_memory["topic_results"] = {}
            
        self.shared_memory["topic_results"][self.topic] = self.result
        
        logger.info(f"Topic processing completed for '{self.topic}'")
        logger.debug(f"Generated {len(self.result['qa_pairs'])} Q&A pairs and {len(self.result.get('transformed_content', ''))} characters of transformed content")
        
        return self.result


if __name__ == "__main__":
    # Test with a sample topic and transcript
    test_topic = "Machine Learning Basics"
    test_transcript = """
    In this video, we're going to talk about machine learning and its applications. 
    Machine learning is a subset of artificial intelligence that focuses on building systems 
    that learn from data. Unlike traditional programming where you explicitly program rules, 
    in machine learning, you train models on data and they learn patterns.
    
    There are several types of machine learning. First, supervised learning, where the model 
    is trained on labeled data. For example, you might have images labeled as "cat" or "dog" 
    and the model learns to distinguish between them. Second, unsupervised learning, where 
    the model finds patterns in unlabeled data. Clustering is a common unsupervised learning task.
    
    Deep learning is a subset of machine learning that uses neural networks with many layers. 
    These deep neural networks have revolutionized fields like computer vision and natural 
    language processing. For instance, convolutional neural networks (CNNs) are excellent at 
    image recognition tasks.
    """
    
    # Create and run the node
    test_rubric = {
        "rubric_id": "structured_digest",
        "name": "Structured Knowledge Digest",
        "confidence": 85
    }
    
    node = TopicProcessorNode(
        topic=test_topic, 
        transcript=test_transcript,
        selected_rubric=test_rubric
    )
    result = node.run()
    
    # Print the results
    if "error" not in result:
        print("\nTopic Processing Results:")
        print(f"Topic: {result['topic_results'][test_topic]['topic']}")
        print(f"Q&A Pairs: {len(result['topic_results'][test_topic]['qa_pairs'])}")
        for i, qa in enumerate(result['topic_results'][test_topic]['qa_pairs']):
            print(f"  Q{i+1}: {qa.get('question', '')}")
            print(f"  A{i+1}: {qa.get('answer', '')[:100]}...")
        print(f"Transformed Content: {result['topic_results'][test_topic]['transformed_content'][:200]}...")
    else:
        print(f"Error: {result['error']}")
