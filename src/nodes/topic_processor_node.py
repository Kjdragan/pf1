"""
Topic Processor Node for YouTube Video Summarizer.
Processes a single topic with Q&A generation and ELI5 transformation.
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

class TopicProcessorNode(BaseNode):
    """
    Node for processing a single topic, including Q&A generation and ELI5 transformation.
    This node is designed to be used as part of a Map-Reduce pattern.
    """
    
    def __init__(self, shared_memory=None, topic=None, transcript=None, questions_per_topic=3):
        """
        Initialize the node with topic and transcript.
        
        Args:
            shared_memory (dict): Shared memory dictionary (optional)
            topic (str): The topic to process
            transcript (str): The video transcript
            questions_per_topic (int): Number of questions to generate per topic
        """
        super().__init__(shared_memory or {})
        self.topic = topic
        self.transcript = transcript
        self.questions_per_topic = questions_per_topic
        self.result = {
            "topic": topic,
            "qa_pairs": [],
            "eli5_content": ""
        }
        logger.debug(f"TopicProcessorNode initialized for topic: {topic}")
    
    def prep(self):
        """
        Prepare for execution by checking if topic and transcript are available.
        """
        # If topic and transcript were not provided in constructor, try to get from shared memory
        if self.topic is None and "current_topic" in self.shared_memory:
            self.topic = self.shared_memory["current_topic"]
            
        if self.transcript is None and "transcript" in self.shared_memory:
            self.transcript = self.shared_memory["transcript"]
            
        if self.topic is None:
            error_msg = "No topic provided for processing"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if self.transcript is None:
            error_msg = "No transcript provided for processing"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info(f"Processing topic: {self.topic}")
    
    def exec(self):
        """
        Execute topic processing: generate Q&A pairs and ELI5 explanation.
        """
        # Step 1: Generate Q&A pairs
        self._generate_qa_pairs()
        
        # Step 2: Create ELI5 explanation
        self._create_eli5_explanation()
    
    def _generate_qa_pairs(self):
        """
        Generate Q&A pairs for the topic.
        """
        logger.info(f"Generating Q&A pairs for topic: {self.topic}")
        
        # Create prompt for Q&A generation
        prompt = textwrap.dedent(f"""
        You are an expert at creating educational content for videos.
        
        I'll provide you with a transcript from a YouTube video and a specific topic from that video.
        Your task is to:
        1. Generate {self.questions_per_topic} insightful questions about this topic
        2. Provide clear, accurate answers to each question based on the transcript
        3. Make sure the questions cover different aspects of the topic
        4. Ensure answers are based only on information in the transcript
        
        Topic: {self.topic}
        
        Transcript:
        {self.transcript[:4000]}...
        
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
            logger.debug(f"Calling LLM for Q&A generation on topic '{self.topic}'")
            response = call_llm(prompt, temperature=0.7, max_tokens=1000)
            logger.debug(f"LLM response for Q&A generation: {response[:100]}...")
            
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
                    self.result["qa_pairs"] = qa_pairs
                    logger.info(f"Generated {len(qa_pairs)} Q&A pairs for topic '{self.topic}'")
                    for i, qa in enumerate(qa_pairs):
                        logger.debug(f"  Q{i+1}: {qa.get('question', '')}")
                        logger.debug(f"  A{i+1}: {qa.get('answer', '')[:100]}...")
                else:
                    logger.warning(f"Expected list but got {type(qa_pairs)} from LLM")
                    self.result["qa_pairs"] = []
            except json.JSONDecodeError:
                logger.warning(f"Could not parse LLM response as JSON: {cleaned_response[:200]}...")
                # Try to extract Q&A pairs from text response
                extracted_qa = self._extract_qa_from_text(cleaned_response)
                self.result["qa_pairs"] = extracted_qa
                logger.info(f"Extracted {len(extracted_qa)} Q&A pairs from non-JSON response")
        except Exception as e:
            logger.error(f"Error generating Q&A pairs for topic '{self.topic}': {str(e)}")
            self.result["qa_pairs"] = []
    
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
    
    def _create_eli5_explanation(self):
        """
        Create an ELI5 (Explain Like I'm 5) explanation for the topic.
        """
        logger.info(f"Creating ELI5 explanation for topic: {self.topic}")
        
        # Get Q&A pairs for context
        qa_text = ""
        for qa in self.result["qa_pairs"]:
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
        
        Topic: {self.topic}
        
        Q&A Context:
        {qa_text}
        
        Respond with ONLY the child-friendly explanation, without any introduction or meta-text.
        """)
        
        # Call LLM to generate ELI5 explanation
        try:
            logger.debug(f"Calling LLM for ELI5 transformation on topic '{self.topic}'")
            response = call_llm(prompt, temperature=0.7, max_tokens=500)
            logger.debug(f"LLM response for ELI5 transformation: {response[:100]}...")
            
            # Clean up the response
            explanation = response.strip()
            
            # Store the ELI5 explanation
            self.result["eli5_content"] = explanation
            logger.info(f"Generated ELI5 explanation for topic '{self.topic}' ({len(explanation)} characters)")
            
        except Exception as e:
            error_msg = f"Error creating ELI5 explanation for topic '{self.topic}': {str(e)}"
            logger.error(error_msg)
            self.result["eli5_content"] = f"Sorry, I couldn't create a simple explanation for {self.topic}."
    
    def post(self):
        """
        Post-process and return the results.
        """
        # Store the results in shared memory if needed
        if "topic_results" not in self.shared_memory:
            self.shared_memory["topic_results"] = {}
            
        self.shared_memory["topic_results"][self.topic] = self.result
        
        logger.info(f"Topic processing completed for '{self.topic}'")
        logger.debug(f"Generated {len(self.result['qa_pairs'])} Q&A pairs and {len(self.result['eli5_content'])} characters of ELI5 content")
        
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
    node = TopicProcessorNode(topic=test_topic, transcript=test_transcript)
    result = node.run()
    
    # Print the results
    logger.info("\nTopic Processing Results:")
    logger.info(f"Topic: {result['topic']}")
    logger.info(f"Q&A Pairs: {len(result['qa_pairs'])}")
    for i, qa in enumerate(result['qa_pairs']):
        logger.info(f"  Q{i+1}: {qa.get('question', '')}")
        logger.info(f"  A{i+1}: {qa.get('answer', '')[:100]}...")
    logger.info(f"ELI5 Explanation: {result['eli5_content']}")
