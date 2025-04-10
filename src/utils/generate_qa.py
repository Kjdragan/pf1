"""
Utility to generate Q&A pairs for topics extracted from video content.

This module takes topics and transcript data to generate relevant
question and answer pairs that enhance understanding of the video content.
Uses OpenAI's structured output capabilities to ensure consistent formatting.
"""

import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from .call_llm import call_llm
from src.utils.logger import logger

# Initialize OpenAI client
client = OpenAI()

# Define Pydantic models for Q&A pairs
class QAPair(BaseModel):
    """Model for a question and answer pair"""
    question: str = Field(..., description="Clear, specific question about the topic")
    answer: str = Field(..., description="Detailed, specific answer with information from the transcript")

class QAPairList(BaseModel):
    """Model for a list of Q&A pairs"""
    qa_pairs: List[QAPair] = Field(..., description="List of question and answer pairs")

def generate_qa_pairs(topic: str, transcript: str, num_pairs: int = 3) -> List[Dict[str, str]]:
    """
    Generate Q&A pairs for a specific topic based on the video transcript.
    Uses OpenAI's structured output capabilities for reliable formatting.
    
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
    
    try:
        # Use OpenAI's Responses API with structured output
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": f"You are an expert educational content creator. Focus specifically on the topic '{topic}'. Generate {num_pairs} insightful question and answer pairs that cover key information from the transcript. Each answer should be 3-5 sentences with specific information."},
                {"role": "user", "content": f"For the topic '{topic}', create {num_pairs} question and answer pairs based on this transcript sample:\n\n{transcript_sample}"}
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "topic_qa_pairs",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "qa_pairs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {
                                            "type": "string", 
                                            "description": f"Clear, specific question about {topic}"
                                        },
                                        "answer": {
                                            "type": "string",
                                            "description": "Detailed, specific answer with information from the transcript"
                                        }
                                    },
                                    "required": ["question", "answer"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["qa_pairs"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )
        
        # Parse the structured output response
        qa_results = json.loads(response.output_text)
        qa_pairs = qa_results.get("qa_pairs", [])
        
        # Verify we got the expected format
        if qa_pairs and len(qa_pairs) > 0:
            logger.info(f"Generated {len(qa_pairs)} Q&A pairs for topic: {topic} using structured output")
            
            # Limit to requested number of pairs
            if len(qa_pairs) > num_pairs:
                qa_pairs = qa_pairs[:num_pairs]
                
            return qa_pairs
        else:
            logger.warning(f"No valid Q&A pairs found for topic: {topic}")
            return get_fallback_qa_pairs(topic)
            
    except Exception as e:
        logger.exception(f"Error generating Q&A pairs for topic {topic}: {str(e)}")
        # If we have error details, log them
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                logger.error(f"API error details: {e.response.json()}")
            except:
                pass
        return get_fallback_qa_pairs(topic)

def generate_whole_content_qa(topics: List[str], transcript: str, num_pairs: int = 5) -> List[Dict[str, str]]:
    """
    Generate Q&A pairs for the entire content based on all topics and the transcript.
    This produces more comprehensive Q&A pairs that span across multiple topics.
    Uses OpenAI's structured output capabilities for reliable formatting.
    
    Args:
        topics (List[str]): List of all topics extracted from the video
        transcript (str): The complete video transcript content
        num_pairs (int): Number of Q&A pairs to generate (default: 5)
        
    Returns:
        List[Dict[str, str]]: List of dictionaries containing 'question' and 'answer' pairs
    """
    logger.info(f"Generating {num_pairs} comprehensive Q&A pairs spanning all topics")
    
    # Create a sample of the transcript if it's too long
    transcript_sample = transcript[:6000] if len(transcript) > 6000 else transcript
    
    # Format the topics list for a cleaner prompt
    topics_text = ", ".join(topics)
    
    try:
        # Use OpenAI's Responses API with structured output
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {"role": "system", "content": f"You are an expert educational content creator. Generate {num_pairs} comprehensive Q&A pairs that cover the main themes across these topics: {topics_text}. Each answer should be 4-6 sentences with specific information from the transcript."},
                {"role": "user", "content": f"Create {num_pairs} insightful question and answer pairs for these topics based on this transcript sample:\n\n{transcript_sample}"}
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "qa_pairs",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "qa_pairs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question": {
                                            "type": "string", 
                                            "description": "Clear, specific question about important themes in the video"
                                        },
                                        "answer": {
                                            "type": "string",
                                            "description": "Detailed, comprehensive answer with specific information from the transcript"
                                        }
                                    },
                                    "required": ["question", "answer"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["qa_pairs"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )
        
        # Parse the structured output response
        qa_results = json.loads(response.output_text)
        qa_pairs = qa_results.get("qa_pairs", [])
        
        # Verify we got the expected format
        if qa_pairs and len(qa_pairs) > 0:
            logger.info(f"Successfully generated {len(qa_pairs)} comprehensive Q&A pairs using structured output")
            
            # Limit to requested number of pairs
            if len(qa_pairs) > num_pairs:
                qa_pairs = qa_pairs[:num_pairs]
                
            return qa_pairs
        else:
            logger.warning("No valid Q&A pairs found in structured output response")
            return get_fallback_comprehensive_qa(topics)
            
    except Exception as e:
        logger.exception(f"Error generating comprehensive Q&A pairs: {str(e)}")
        # If we have error details, log them
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                logger.error(f"API error details: {e.response.json()}")
            except:
                pass
        return get_fallback_comprehensive_qa(topics)

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

def get_fallback_comprehensive_qa(topics: List[str]) -> List[Dict[str, str]]:
    """
    Create fallback comprehensive Q&A pairs when the LLM call fails.
    
    Args:
        topics (List[str]): List of topics to reference in the fallback Q&A
        
    Returns:
        List[Dict[str, str]]: Basic fallback comprehensive Q&A pairs
    """
    logger.info("Using fallback comprehensive Q&A pairs")
    
    # Join topics with commas and 'and' for the last one
    if len(topics) > 1:
        topics_text = ", ".join(topics[:-1]) + ", and " + topics[-1]
    else:
        topics_text = topics[0] if topics else "the video topics"
    
    return [
        {
            "question": f"What are the key takeaways from this video?",
            "answer": f"This video covers several important topics including {topics_text}. The specific details would be extracted from the video transcript."
        },
        {
            "question": "How do these topics relate to each other?",
            "answer": "The topics in this video are interconnected through several themes. This answer would explain the relationships between the main ideas presented."
        },
        {
            "question": "What is the significance of these issues?",
            "answer": "These topics have important implications for several areas. This answer would provide context about why these issues matter."
        },
        {
            "question": "What are some practical applications of this information?",
            "answer": "The concepts discussed in this video have several practical applications. This answer would outline how this information might be applied."
        },
        {
            "question": "What further questions might arise from this topic?",
            "answer": "This video raises several important questions for further consideration. This answer would suggest areas for additional exploration."
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
