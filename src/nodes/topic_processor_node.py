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
    
    def __init__(self, shared_memory=None):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary containing:
                - topic: The topic to process
                - transcript: The video transcript
                - selected_rubric: The selected rubric information
                - questions_per_topic: Number of questions to generate per topic
                - no_qa (optional): Whether to disable Q&A generation
                - knowledge_level (optional): The knowledge level for the topic
        """
        super().__init__(shared_memory or {})
        self.topic = self.shared_memory.get("topic")
        self.transcript = self.shared_memory.get("transcript")
        self.selected_rubric = self.shared_memory.get("selected_rubric")
        self.questions_per_topic = self.shared_memory.get("questions_per_topic", 3)
        self.no_qa = self.shared_memory.get("no_qa", False)
        self.knowledge_level = self.shared_memory.get("knowledge_level")
        logger.debug(f"TopicProcessorNode initialized for topic: {self.topic}")
    
    def prep(self):
        """
        Prepare for execution by checking if topic, transcript, and rubric are available.
        """
        if not self.topic:
            error_msg = "No topic specified for processing"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        if not self.transcript:
            error_msg = "No transcript provided for topic processing"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        if not self.selected_rubric:
            error_msg = "No rubric selected for topic transformation"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
        
        logger.info(f"Preparing to process topic: {self.topic}")
        logger.debug(f"Selected rubric: {self.selected_rubric['name']}")
        logger.debug(f"Q&A generation: {'Disabled' if self.no_qa else 'Enabled'}")
    
    def exec(self):
        """
        Execute topic processing, including Q&A generation and content transformation.
        """
        if "error" in self.shared_memory:
            return
        
        # Process the topic
        try:
            # Skip Q&A generation for individual topics
            qa_pairs = []
            
            # Apply the selected rubric
            transformed_content = self._apply_rubric_transformation()
            logger.info(f"Applied rubric '{self.selected_rubric['name']}' to topic: {self.topic}")
            
            # Store the results
            self.shared_memory["qa_pairs"] = qa_pairs
            self.shared_memory["transformed_content"] = transformed_content
            
        except Exception as e:
            error_msg = f"Error processing topic '{self.topic}': {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
    
    def _generate_qa_pairs(self):
        """
        Generate Q&A pairs for the topic.
        
        Returns:
            list: List of Q&A pairs
        """
        logger.info(f"Generating {self.questions_per_topic} Q&A pairs for topic: {self.topic}")
        
        try:
            # Call the generate_qa_pairs utility
            qa_pairs = generate_qa_pairs(self.topic, self.transcript, self.questions_per_topic)
            return qa_pairs
            
        except Exception as e:
            logger.exception(f"Error generating Q&A pairs for topic {self.topic}: {str(e)}")
            return []
    
    def _apply_rubric_transformation(self):
        """
        Apply the selected rubric transformation to the topic.
        
        Returns:
            str: The transformed content
        """
        try:
            logger.debug(f"Applying rubric '{self.selected_rubric['name']}' to topic: {self.topic}")
            
            # Format content dictionary as expected by apply_rubric
            # No need for Q&A pairs since we're not generating them for individual topics
            content = {
                "topics": [self.topic],
                "transcript": self.transcript
            }
            
            # Get knowledge level from the selected rubric if available
            knowledge_level = None
            if self.selected_rubric and 'knowledge_level' in self.selected_rubric:
                knowledge_level = self.selected_rubric['knowledge_level']
            elif self.knowledge_level is not None:
                knowledge_level = self.knowledge_level
            
            # Log the knowledge level being used
            logger.debug(f"Using knowledge level: {knowledge_level if knowledge_level is not None else 'default'}")
            
            # Call the apply_rubric utility with correct parameters
            transformed = apply_rubric(
                content=content,
                rubric_type=self.selected_rubric.get("rubric_id", "insightful_conversational"),
                knowledge_level=knowledge_level
            )
            
            # Extract the transformed content for this topic
            if transformed and "transformed_content" in transformed:
                return transformed["transformed_content"].get(self.topic, f"Error: No transformed content for {self.topic}")
            return f"Error: Failed to transform content for {self.topic}"
            
        except Exception as e:
            logger.exception(f"Error applying rubric to topic {self.topic}: {str(e)}")
            return f"Error transforming content for {self.topic}: {str(e)}"
    
    def post(self):
        """
        Post-process the topic results.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Topic Processor Node: {self.shared_memory['error']}")
            return
        
        transformed_content_length = len(self.shared_memory.get("transformed_content", ""))
        
        logger.info(f"Topic Processor completed for: {self.topic}")
        logger.info(f"Transformed content length: {transformed_content_length} characters")


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
    
    shared_memory = {
        "topic": test_topic,
        "transcript": test_transcript,
        "selected_rubric": test_rubric,
        "questions_per_topic": 3,
        "no_qa": False
    }
    
    node = TopicProcessorNode(shared_memory)
    node.run()
    
    # Print the results
    if "error" not in shared_memory:
        print("\nTopic Processing Results:")
        print(f"Topic: {shared_memory['topic']}")
        print(f"Q&A Pairs: {len(shared_memory['qa_pairs'])}")
        for i, qa in enumerate(shared_memory['qa_pairs']):
            print(f"  Q{i+1}: {qa.get('question', '')}")
            print(f"  A{i+1}: {qa.get('answer', '')[:100]}...")
        print(f"Transformed Content: {shared_memory['transformed_content'][:200]}...")
    else:
        print(f"Error: {shared_memory['error']}")
