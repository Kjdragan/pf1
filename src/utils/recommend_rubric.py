"""
Utility to recommend appropriate transformation rubrics based on video content.

This module analyzes the video transcript and extracted topics to suggest
appropriate document transformation styles (rubrics) along with confidence
scores and justifications.
"""

import json
from typing import Dict, List, Tuple
from .call_llm import call_llm
from src.utils.logger import logger

# Define the available rubrics with their characteristics
RUBRICS = {
    "insightful_conversational": {
        "name": "Insightful Conversational Summary",
        "description": "Moderate compression preserving conversational tone, authentic voice, retains quotes and key analogies"
    },
    "analytical_narrative": {
        "name": "Analytical Narrative Transformation",
        "description": "Adds analytical commentary clearly separate from original ideas, preserves core arguments"
    },
    "educational_extraction": {
        "name": "In-depth Educational Extraction",
        "description": "Lower compression, aimed at replicating detailed educational content, preserves definitions and concepts"
    },
    "structured_digest": {
        "name": "Structured Knowledge Digest",
        "description": "High compression, concise knowledge delivery, organized bullet points, clear headings"
    },
    "emotion_context_rich": {
        "name": "Emotion and Context-rich Narration",
        "description": "Captures emotional depth, authentic voice, and nuanced context, emphasizes emotional narrative"
    },
    "top_n_knowledge": {
        "name": "Top N Knowledge Extraction",
        "description": "Summarize content into enumerated, prioritized lists, maintains sophisticated language"
    },
    "checklist_actionable": {
        "name": "Checklist or Actionable Summary",
        "description": "Provide concise, actionable steps, structured as task-oriented checklists"
    },
    "contrarian_insights": {
        "name": "Contrarian Insights (Myth-Busting)",
        "description": "Identify and clarify misconceptions explicitly, structured as myths versus realities"
    },
    "key_quotes": {
        "name": "Key Quotes or Notable Statements",
        "description": "Extract direct quotes preserving exact original wording and impact, minimal compression"
    },
    "eli5": {
        "name": "ELI5 (Explain Like I'm Five)",
        "description": "Simplify complex topics for beginner understanding, simple language and basic analogies"
    }
}

def recommend_rubric(transcript: str, topics: List[str]) -> List[Dict]:
    """
    Analyze content and recommend appropriate transformation rubrics.
    
    Args:
        transcript (str): The video transcript
        topics (List[str]): List of extracted topics
        
    Returns:
        List[Dict]: A list of recommended rubrics with confidence scores and justifications
    """
    logger.info("Recommending appropriate rubrics based on content")
    
    # Create a sample of the transcript if it's too long
    transcript_sample = transcript[:3000] if len(transcript) > 3000 else transcript
    
    # Prepare a prompt for the LLM
    prompt = f"""
You are an expert content analyst. Given a video transcript and its main topics, 
recommend the most appropriate document transformation rubrics from the provided list.
For each recommendation, provide a confidence score (0-100) and a brief justification.

Video Transcript Sample:
{transcript_sample}

Main Topics:
{json.dumps(topics, indent=2)}

Available Rubrics:
{json.dumps({k: v for k, v in RUBRICS.items()}, indent=2)}

Analyze the content and recommend 3-5 rubrics that would be most appropriate.
For each recommendation, provide:
1. The rubric ID (key from the available rubrics)
2. A confidence score (0-100)
3. A brief justification explaining why this rubric is appropriate for this content

Your response MUST follow this exact format:
```json
[
  {{
    "rubric_id": "rubric_key",
    "confidence": 85,
    "justification": "Brief explanation of why this rubric is appropriate"
  }},
  ...additional recommendations...
]
```

CRITICAL REQUIREMENTS:
1. Start your response with ```json
2. End your response with ```
3. Use ONLY valid JSON with double quotes around keys and string values
4. Do not include any text outside the JSON code block
5. Do not use single quotes or trailing commas
"""
    
    try:
        # Call the LLM to analyze and recommend rubrics
        response = call_llm(prompt)
        
        # Parse the response (assuming it's valid JSON)
        try:
            # Extract JSON from response if wrapped in markdown code blocks
            if "```json" in response and "```" in response.split("```json", 1)[1]:
                json_str = response.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in response:
                # Try to extract from any code block
                json_str = response.split("```", 1)[1].split("```", 1)[0].strip()
            else:
                # Use the whole response if no code blocks are found
                json_str = response.strip()
            
            # Parse the JSON response
            recommendations = json.loads(json_str)
            logger.info(f"Successfully received {len(recommendations)} rubric recommendations")
            
            # Validate and enrich the recommendations
            validated_recommendations = []
            for rec in recommendations:
                if isinstance(rec, dict) and "rubric_id" in rec and rec["rubric_id"] in RUBRICS:
                    # Add the full name and description to the recommendation
                    rec["name"] = RUBRICS[rec["rubric_id"]]["name"]
                    rec["description"] = RUBRICS[rec["rubric_id"]]["description"]
                    
                    # Ensure confidence is an integer
                    if "confidence" in rec and isinstance(rec["confidence"], (int, float)):
                        rec["confidence"] = int(rec["confidence"])
                    else:
                        rec["confidence"] = 70  # Default confidence
                        
                    validated_recommendations.append(rec)
                else:
                    logger.warning(f"Skipping invalid recommendation format: {rec}")
            
            if validated_recommendations:
                # Sort by confidence score in descending order
                validated_recommendations.sort(key=lambda x: x["confidence"], reverse=True)
                return validated_recommendations
            else:
                logger.warning("No valid recommendations found")
                return get_default_recommendations()
            
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse LLM response as JSON. Error: {str(json_err)}")
            logger.debug(f"Response that failed parsing: {response[:200]}...")
            # Fallback to default recommendations
            return get_default_recommendations()
            
    except Exception as e:
        logger.exception(f"Error recommending rubrics: {str(e)}")
        return get_default_recommendations()

def get_default_recommendations() -> List[Dict]:
    """
    Provide default rubric recommendations when the LLM call fails.
    
    Returns:
        List[Dict]: A list of default recommended rubrics
    """
    logger.info("Using default rubric recommendations")
    
    default_recs = [
        {
            "rubric_id": "insightful_conversational",
            "name": RUBRICS["insightful_conversational"]["name"],
            "description": RUBRICS["insightful_conversational"]["description"],
            "confidence": 80,
            "justification": "Default recommendation as this format works well for most content types."
        },
        {
            "rubric_id": "structured_digest",
            "name": RUBRICS["structured_digest"]["name"],
            "description": RUBRICS["structured_digest"]["description"],
            "confidence": 75,
            "justification": "Default recommendation as this provides clear, organized information."
        },
        {
            "rubric_id": "eli5",
            "name": RUBRICS["eli5"]["name"],
            "description": RUBRICS["eli5"]["description"],
            "confidence": 70,
            "justification": "Default recommendation as simplified explanations are useful for complex topics."
        }
    ]
    
    return default_recs

if __name__ == "__main__":
    # Simple test case
    test_transcript = "This is a sample transcript about machine learning and AI technologies."
    test_topics = ["Introduction to Machine Learning", "Neural Networks", "AI Applications"]
    
    recommendations = recommend_rubric(test_transcript, test_topics)
    print(json.dumps(recommendations, indent=2))
