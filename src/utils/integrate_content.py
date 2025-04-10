"""
Utility to integrate individual topic transformations into a cohesive document.
"""
from typing import Dict, List, Any
import json
from src.utils.call_llm import call_llm
from src.utils.logger import logger

def integrate_content(
    transformed_content: Dict[str, str], 
    topics: List[str], 
    selected_rubric: Dict[str, Any],
    qa_pairs: Dict[str, List[Dict[str, str]]] = None,
    knowledge_level: int = 5
) -> str:
    """
    Transform individual topic outputs into a cohesive document.
    
    Args:
        transformed_content (Dict[str, str]): Dictionary mapping topics to their transformed content
        topics (List[str]): List of topics in the video
        selected_rubric (Dict[str, Any]): The selected transformation rubric
        qa_pairs (Dict[str, List[Dict[str, str]]], optional): Q&A pairs organized by topic
        knowledge_level (int, optional): Knowledge augmentation level (1-10)
        
    Returns:
        str: A cohesive document integrating all topic transformations
    """
    logger.info("Integrating individual topic transformations into a cohesive document")
    
    # Prepare the content for integration
    content_sections = []
    for topic in topics:
        if topic in transformed_content:
            content_sections.append({
                "topic": topic,
                "content": transformed_content[topic]
            })
    
    # Prepare the prompt for the LLM
    prompt = f"""
    You are an expert content editor. You need to transform multiple separate topic sections into a single cohesive document.
    
    # ORIGINAL CONTENT SECTIONS:
    {json.dumps(content_sections, indent=2)}
    
    # INSTRUCTIONS:
    1. Create a cohesive document that integrates all the topics naturally.
    2. Eliminate repetitive phrases and redundant information.
    3. Ensure smooth transitions between topics.
    4. Maintain the overall style and tone of the original content.
    5. Do not introduce new factual information not present in the original sections.
    6. The document should read as a single, unified piece rather than separate sections.
    7. Do not include section headers or explicit topic divisions unless they flow naturally.
    8. Do not include phrases like "In this episode" or "In today's breakdown" more than once.
    9. Knowledge level for external context is {knowledge_level}/10 (where 1 is minimal and 10 is extensive).
    
    # RUBRIC STYLE:
    The content follows the "{selected_rubric.get('name', 'Standard')}" style.
    
    # OUTPUT FORMAT:
    Provide only the integrated content as plain text with appropriate paragraph breaks. Do not include any meta-commentary.
    """
    
    try:
        # Call the LLM to integrate the content
        integrated_content = call_llm(prompt)
        logger.info(f"Successfully integrated content ({len(integrated_content)} characters)")
        return integrated_content
    except Exception as e:
        logger.error(f"Failed to integrate content: {str(e)}")
        # Fallback: concatenate the transformed content with simple transitions
        fallback_content = ""
        for i, topic in enumerate(topics):
            if topic in transformed_content:
                if i > 0:
                    fallback_content += "\n\n"
                fallback_content += transformed_content[topic]
        
        logger.warning(f"Using fallback integration method ({len(fallback_content)} characters)")
        return fallback_content


if __name__ == "__main__":
    # Test with sample data
    test_transformed_content = {
        "Legal Background": "In this episode of the Legal Breakdown, we examine a noteworthy development in the legal contest involving Donald Trump and the standing of states in legal challenges. Initially, a federal trial court ruled unfavorably against Trump's administration, declaring the termination of probationary employees unlawful and issuing a preliminary injunction to reinstate these individuals.",
        "Court Ruling": "The Fourth Circuit Court of Appeals has now overturned this injunction in a 2-1 decision. What is particularly intriguing here is that the appeals court refrained from making a determination regarding the legality of the terminations executed by the Trump administration.",
        "Implications": "This decision represents a provisional victory for the Trump administration and a setback for the employees, who were in the midst of being reinstated. The situation remains dynamic, but as it currently stands, the appeals court decision is a pivotal juncture, underscoring the intricate nature of legal standings in state-involved challenges."
    }
    
    test_topics = ["Legal Background", "Court Ruling", "Implications"]
    
    test_rubric = {
        "name": "Analytical Narrative Transformation",
        "description": "Adds analytical commentary clearly separate from original ideas"
    }
    
    integrated = integrate_content(test_transformed_content, test_topics, test_rubric)
    print("\nIntegrated Content:")
    print(integrated)
