"""
Q&A Generation Node for YouTube Video Summarizer.
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

class QAGenerationNode(BaseNode):
    """
    Node for generating Q&A pairs for each topic in the video.
    """
    
    def __init__(self, shared_memory=None, questions_per_topic=3):
        """
        Initialize the node with shared memory.
        
        Args:
            shared_memory (dict): Shared memory dictionary
            questions_per_topic (int): Number of questions to generate per topic
        """
        super().__init__(shared_memory)
        self.questions_per_topic = questions_per_topic
        self.qa_pairs = {}
        logger.debug(f"QAGenerationNode initialized with questions_per_topic={questions_per_topic}")
    
    def prep(self):
        """
        Prepare for execution by checking if topics and transcript exist in shared memory.
        """
        if "topics" not in self.shared_memory:
            error_msg = "Topics not found in shared memory"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if "transcript" not in self.shared_memory:
            error_msg = "Transcript not found in shared memory"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if "error" in self.shared_memory:
            logger.warning(f"Skipping Q&A Generation due to previous error: {self.shared_memory['error']}")
            return
        
        topics_count = len(self.shared_memory['topics'])
        logger.info(f"Generating Q&A pairs for {topics_count} topics")
        logger.debug(f"Topics: {self.shared_memory['topics']}")
    
    def exec(self):
        """
        Execute Q&A generation for each topic.
        """
        if "error" in self.shared_memory:
            return
            
        topics = self.shared_memory["topics"]
        transcript = self.shared_memory["transcript"]
        
        # Process each topic to generate Q&A pairs
        for i, topic in enumerate(topics):
            logger.info(f"Generating Q&A pairs for topic {i+1}/{len(topics)}: {topic}")
            
            # Create prompt for Q&A generation
            prompt = textwrap.dedent(f"""
            You are an expert at creating educational content for videos.
            
            I'll provide you with a transcript from a YouTube video and a specific topic from that video.
            Your task is to:
            1. Generate {self.questions_per_topic} insightful questions about this topic
            2. Provide clear, accurate answers to each question based on the transcript
            3. Make sure the questions cover different aspects of the topic
            4. Ensure answers are based only on information in the transcript
            
            Topic: {topic}
            
            Transcript:
            {transcript[:4000]}...
            
            Respond with ONLY a JSON array of question-answer objects. For example:
            [
                {{
                    "question": "What is the main purpose of X?",
                    "answer": "According to the video, the main purpose of X is..."
                }},
                {{
                    "question": "How does Y relate to Z?",
                    "answer": "The video explains that Y and Z are connected through..."
                }}
            ]
            """)
            
            # Call LLM to generate Q&A pairs
            try:
                logger.debug(f"Calling LLM for topic '{topic}'")
                response = call_llm(prompt, temperature=0.7, max_tokens=1000)
                logger.debug(f"LLM response for topic '{topic}': {response[:100]}...")
                
                # Clean up the response to extract just the JSON array
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response.split("```json")[1]
                elif cleaned_response.startswith("```"):
                    cleaned_response = cleaned_response.split("```")[1]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response.split("```")[0]
                
                # Try to parse as JSON, but handle errors gracefully
                try:
                    qa_pairs = json.loads(cleaned_response)
                    if isinstance(qa_pairs, list):
                        self.qa_pairs[topic] = qa_pairs
                        logger.info(f"Generated {len(qa_pairs)} Q&A pairs for topic '{topic}'")
                        for j, qa in enumerate(qa_pairs):
                            logger.debug(f"  Q{j+1}: {qa.get('question', '')}")
                            logger.debug(f"  A{j+1}: {qa.get('answer', '')[:100]}...")
                    else:
                        logger.warning(f"Expected list but got {type(qa_pairs)} from LLM for topic '{topic}'")
                        self.qa_pairs[topic] = []
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse LLM response as JSON for topic '{topic}': {cleaned_response[:200]}...")
                    # Try to extract Q&A pairs from text response
                    extracted_qa = self._extract_qa_from_text(cleaned_response)
                    self.qa_pairs[topic] = extracted_qa
                    logger.info(f"Extracted {len(extracted_qa)} Q&A pairs from non-JSON response for topic '{topic}'")
            except Exception as e:
                logger.error(f"Error calling LLM for topic '{topic}': {str(e)}")
                self.qa_pairs[topic] = []
    
    def _extract_qa_from_text(self, text):
        """
        Attempt to extract Q&A pairs from non-JSON text.
        
        Args:
            text (str): Text containing Q&A pairs
            
        Returns:
            list: List of Q&A pair dictionaries
        """
        logger.debug("Attempting to extract Q&A pairs from non-JSON text")
        lines = text.split("\n")
        qa_pairs = []
        current_question = None
        current_answer = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with Q: or Question:
            if line.startswith(("Q:", "Question:")):
                # If we have a previous question, save it
                if current_question:
                    qa_pairs.append({
                        "question": current_question,
                        "answer": current_answer.strip()
                    })
                
                # Extract new question
                current_question = line.split(":", 1)[1].strip()
                current_answer = ""
            # Check if line starts with A: or Answer:
            elif line.startswith(("A:", "Answer:")) and current_question:
                current_answer += line.split(":", 1)[1].strip() + " "
            # Otherwise, add to current answer if we have a question
            elif current_question:
                current_answer += line + " "
        
        # Add the last Q&A pair if exists
        if current_question:
            qa_pairs.append({
                "question": current_question,
                "answer": current_answer.strip()
            })
            
        logger.debug(f"Extracted {len(qa_pairs)} Q&A pairs from text")
        return qa_pairs
    
    def post(self):
        """
        Post-process and store the generated Q&A pairs in shared memory.
        """
        if "error" in self.shared_memory:
            logger.error(f"Error in Q&A Generation Node: {self.shared_memory['error']}")
            return
        
        # Store the Q&A pairs in shared memory
        self.shared_memory["qa_pairs"] = self.qa_pairs
        
        # Print a summary of the generated Q&A pairs
        total_qa_pairs = sum(len(pairs) for pairs in self.qa_pairs.values())
        logger.info(f"Generated a total of {total_qa_pairs} Q&A pairs across {len(self.qa_pairs)} topics")
        
        for topic, pairs in self.qa_pairs.items():
            logger.info(f"  Topic '{topic}': {len(pairs)} Q&A pairs")
        
        logger.info("Q&A Generation Node completed successfully")


if __name__ == "__main__":
    # Test with sample topics and transcript
    test_topics = ["Machine Learning Basics", "Types of Machine Learning", "Applications of AI"]
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
    
    Now let's discuss some applications of machine learning. In healthcare, machine learning 
    is used for disease diagnosis, drug discovery, and personalized medicine. In finance, 
    it's used for fraud detection, algorithmic trading, and credit scoring. In transportation, 
    self-driving cars rely heavily on machine learning algorithms.
    
    Ethical considerations in machine learning include bias in training data, model interpretability, 
    and privacy concerns. It's important to develop responsible AI systems that are fair and transparent.
    """
    
    # Initialize shared memory
    shared_memory = {
        "topics": test_topics,
        "transcript": test_transcript
    }
    
    # Create and run the node
    node = QAGenerationNode(shared_memory)
    updated_memory = node.run()
    
    # Print the results
    logger.info("\nShared Memory after processing:")
    qa_pairs = updated_memory.get("qa_pairs", {})
    for topic, pairs in qa_pairs.items():
        logger.info(f"\nTopic: {topic}")
        for i, qa in enumerate(pairs):
            logger.info(f"  Q{i+1}: {qa.get('question', '')}")
            logger.info(f"  A{i+1}: {qa.get('answer', '')[:100]}...")
