"""
ELI5 (Explain Like I'm 5) Transformation Node for YouTube Video Summarizer.
"""
import sys
import os
import textwrap
import json

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.call_llm import call_llm
from src.utils.logger import logger

class ELI5TransformationNode(BaseNode):
    """
    Node for transforming content into child-friendly explanations (ELI5).
    """
    
    def __init__(self, shared_memory=None):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary
        """
        super().__init__(shared_memory)
        self.eli5_content = {}
    
    def prep(self):
        """
        Prepare for execution by checking if topics and qa_pairs exist in shared memory.
        """
        if "topics" not in self.shared_memory:
            error_msg = "Topics not found in shared memory"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if "qa_pairs" not in self.shared_memory:
            error_msg = "Q&A pairs not found in shared memory"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if "error" in self.shared_memory:
            logger.warning(f"Skipping ELI5 Transformation due to previous error: {self.shared_memory['error']}")
            return
        
        topics_count = len(self.shared_memory['topics'])
        logger.info(f"Transforming content into child-friendly explanations for {topics_count} topics")
        logger.debug(f"Topics: {self.shared_memory['topics']}")
    
    def exec(self):
        """
        Execute ELI5 transformation for each topic and its Q&A pairs.
        """
        if "error" in self.shared_memory:
            return
            
        topics = self.shared_memory["topics"]
        qa_pairs = self.shared_memory["qa_pairs"]
        
        # Process each topic to create ELI5 explanations
        for i, topic in enumerate(topics):
            logger.info(f"Creating ELI5 explanation for topic {i+1}/{len(topics)}: {topic}")
            
            # Get Q&A pairs for this topic
            topic_qa_pairs = qa_pairs.get(topic, [])
            logger.debug(f"Found {len(topic_qa_pairs)} Q&A pairs for topic '{topic}'")
            
            # Combine Q&A pairs into a single text for context
            qa_text = ""
            for qa in topic_qa_pairs:
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                qa_text += f"Q: {question}\nA: {answer}\n\n"
            
            # Create prompt for ELI5 transformation
            prompt = textwrap.dedent(f"""
            You are an expert at explaining complex topics to young children (5-7 years old).
            
            I'll provide you with a topic and some Q&A pairs about that topic from a YouTube video.
            Your task is to:
            1. Create a simple, friendly explanation of the topic that a 5-year-old would understand
            2. Use simple words, short sentences, and concrete examples
            3. Avoid jargon and technical terms
            4. Use analogies to familiar concepts when possible
            5. Keep the explanation under 200 words
            6. Maintain the core information while simplifying the language
            
            Topic: {topic}
            
            Q&A Context:
            {qa_text}
            
            Respond with ONLY the child-friendly explanation, without any introduction or meta-text.
            """)
            
            # Call LLM to generate ELI5 explanation
            try:
                logger.debug(f"Calling LLM for topic '{topic}' ELI5 transformation")
                response = call_llm(prompt, temperature=0.7, max_tokens=500)
                logger.debug(f"LLM response for topic '{topic}' ELI5: {response[:100]}...")
                
                # Clean up the response
                explanation = response.strip()
                
                # Store the ELI5 explanation
                self.eli5_content[topic] = explanation
                logger.info(f"Generated ELI5 explanation for topic '{topic}' ({len(explanation)} characters)")
                
            except Exception as e:
                error_msg = f"Error calling LLM for topic '{topic}': {str(e)}"
                logger.error(error_msg)
                self.eli5_content[topic] = f"Sorry, I couldn't create a simple explanation for {topic}."
    
    def post(self):
        """
        Post-process and store the ELI5 explanations in shared memory.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in ELI5 Transformation Node: {self.shared_memory['error']}")
            return
        
        # Store the ELI5 explanations in shared memory
        self.shared_memory["eli5_content"] = self.eli5_content
        
        # Print a summary of the generated ELI5 explanations
        logger.info(f"Generated ELI5 explanations for {len(self.eli5_content)} topics")
        
        for topic, explanation in self.eli5_content.items():
            preview = explanation[:100] + "..." if len(explanation) > 100 else explanation
            logger.info(f"  Topic '{topic}':")
            logger.info(f"    {preview}")
        
        logger.info("ELI5 Transformation Node completed successfully")


if __name__ == "__main__":
    # Test with sample topics and Q&A pairs
    test_topics = ["Machine Learning Basics", "Types of Machine Learning"]
    test_qa_pairs = {
        "Machine Learning Basics": [
            {
                "question": "What is machine learning?",
                "answer": "Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data. Unlike traditional programming where you explicitly program rules, in machine learning, you train models on data and they learn patterns."
            },
            {
                "question": "Why is machine learning important?",
                "answer": "Machine learning is important because it allows computers to find insights and make predictions without being explicitly programmed. It can handle complex tasks that would be difficult to code manually."
            }
        ],
        "Types of Machine Learning": [
            {
                "question": "What is supervised learning?",
                "answer": "Supervised learning is a type of machine learning where the model is trained on labeled data. For example, you might have images labeled as 'cat' or 'dog' and the model learns to distinguish between them."
            },
            {
                "question": "What is unsupervised learning?",
                "answer": "Unsupervised learning is where the model finds patterns in unlabeled data. Clustering is a common unsupervised learning task where the algorithm groups similar data points together."
            }
        ]
    }
    
    # Initialize shared memory
    shared_memory = {
        "topics": test_topics,
        "qa_pairs": test_qa_pairs
    }
    
    # Create and run the node
    node = ELI5TransformationNode(shared_memory)
    updated_memory = node.run()
    
    # Print the results
    logger.info("\nShared Memory after processing:")
    eli5_content = updated_memory.get("eli5_content", {})
    for topic, explanation in eli5_content.items():
        logger.info(f"\nTopic: {topic}")
        logger.info(explanation)
