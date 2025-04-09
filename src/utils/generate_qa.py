"""
Utility to generate Q&A pairs for topics extracted from video content.

This module takes topics and transcript data to generate relevant
question and answer pairs that enhance understanding of the video content.
"""

import json
from typing import Dict, List, Any
from .call_llm import call_llm
from src.utils.logger import logger

def generate_qa_pairs(topic: str, transcript: str, num_pairs: int = 3) -> List[Dict[str, str]]:
    """
    Generate Q&A pairs for a specific topic based on the video transcript.
    
    Args:
        topic (str): The topic to generate Q&A pairs for
        transcript (str): The video transcript content
        num_pairs (int): Number of Q&A pairs to generate (default: 3)
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing 'question' and 'answer' pairs
    """
    logger.info(f"Generating {num_pairs} Q&A pairs for topic: {topic}")
    
    # Create a sample of the transcript if it's too long
    transcript_sample = transcript[:5000] if len(transcript) > 5000 else transcript
    
    # Prepare a prompt for the LLM
    prompt = f"""
You are an expert educational content creator. Given a topic and video transcript,
generate {num_pairs} insightful question and answer pairs that:
1. Focus specifically on the topic "{topic}"
2. Cover key information present in the transcript
3. Progress from fundamental to more advanced understanding
4. Are clear, concise, and educational

Video Transcript Sample:
{transcript_sample}

For the topic "{topic}", create {num_pairs} question and answer pairs.
Format your response as valid JSON with this structure:
[
  {{
    "question": "Clear, specific question about the topic",
    "answer": "Comprehensive answer based on transcript information"
  }},
  ...
]
"""
    
    try:
        # Call the LLM to generate Q&A pairs
        response = call_llm(prompt)
        
        try:
            # Parse the JSON response
            qa_pairs = json.loads(response)
            logger.info(f"Successfully generated {len(qa_pairs)} Q&A pairs for topic: {topic}")
            return qa_pairs
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON for topic: {topic}")
            # Create a fallback response
            return get_fallback_qa_pairs(topic)
            
    except Exception as e:
        logger.exception(f"Error generating Q&A pairs for topic {topic}: {str(e)}")
        return get_fallback_qa_pairs(topic)

def get_fallback_qa_pairs(topic: str) -> List[Dict[str, str]]:
    """
    Create fallback Q&A pairs when the LLM call fails.
    
    Args:
        topic (str): The topic to create fallback Q&A pairs for
        
    Returns:
        List[Dict[str, str]]: Basic fallback Q&A pairs
    """
    logger.info(f"Using fallback Q&A pairs for topic: {topic}")
    
    return [
        {
            "question": f"What is {topic}?",
            "answer": f"This would provide a definition and overview of {topic}."
        },
        {
            "question": f"Why is {topic} important?",
            "answer": f"This would explain the significance and applications of {topic}."
        },
        {
            "question": f"How does {topic} relate to other concepts in this video?",
            "answer": f"This would describe how {topic} connects to other ideas presented in the video."
        }
    ]

def process_topics_qa(topics: List[str], transcript: str, num_pairs_per_topic: int = 3) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate Q&A pairs for multiple topics from a video transcript.
    
    Args:
        topics (List[str]): List of topics to generate Q&A pairs for
        transcript (str): The video transcript content
        num_pairs_per_topic (int): Number of Q&A pairs to generate per topic (default: 3)
        
    Returns:
        Dict[str, List[Dict[str, str]]]: Dictionary mapping topics to their Q&A pairs
    """
    logger.info(f"Processing Q&A generation for {len(topics)} topics")
    
    qa_results = {}
    
    for topic in topics:
        qa_results[topic] = generate_qa_pairs(topic, transcript, num_pairs_per_topic)
    
    logger.info(f"Completed Q&A generation for {len(qa_results)} topics")
    return qa_results

if __name__ == "__main__":
    # Simple test case
    test_transcript = """
    Machine learning is a subset of artificial intelligence that involves training 
    algorithms to recognize patterns in data. One of the most common applications 
    is in image recognition, where neural networks are trained to identify objects 
    in images. Neural networks are computational models inspired by the human brain's 
    structure, consisting of interconnected nodes or "neurons" that process information 
    in layers. Deep learning is an advanced approach to neural networks with many layers, 
    enabling more complex pattern recognition. Transfer learning is a technique where a 
    pre-trained model is adapted for a new task, saving computational resources and training time.
    """
    
    test_topics = ["Neural Networks", "Transfer Learning"]
    
    # Test generating Q&A pairs for multiple topics
    qa_results = process_topics_qa(test_topics, test_transcript)
    print(json.dumps(qa_results, indent=2))
