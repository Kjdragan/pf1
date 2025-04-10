"""
Rubric Selection Node for YouTube Video Summarizer.

This node facilitates user selection of preferred transformation rubric.
"""
import sys
import os

# Add the project root to the path so we can import from src.utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.nodes.base_node import BaseNode
from src.utils.logger import logger

class RubricSelectionNode(BaseNode):
    """
    Node that facilitates user selection of preferred transformation rubric.
    
    This node:
    1. Reads recommended_rubrics from shared memory
    2. Presents options to the user and captures selection
    3. Writes selected_rubric and audience_level to shared memory
    """
    
    def __init__(self, shared_memory=None):
        """Initialize the RubricSelectionNode."""
        super().__init__(shared_memory)
        logger.info("RubricSelectionNode initialized")
        
        # Default audience level (from design doc)
        self.audience_levels = {
            "sophisticated": "University-level education vocabulary, direct, occasional wit, analytical depth",
            "general": "Mainstream audience, balanced vocabulary, neutral tone",
            "child": "Simplified language, concrete examples (used for ELI5 rubric)"
        }
        self.default_audience = "sophisticated"
        
        # Knowledge augmentation level descriptions
        self.knowledge_level_descriptions = {
            1: "Pure extraction - only information explicitly stated in the video",
            2: "Minimal augmentation - mostly video content with very limited context",
            3: "Low augmentation - video content with occasional clarifications",
            4: "Below average augmentation - video content with helpful clarifications",
            5: "Balanced approach - video content with contextual information",
            6: "Above average augmentation - enhanced video content with context",
            7: "Moderate augmentation - video content with significant context",
            8: "High augmentation - video content with substantial external knowledge",
            9: "Very high augmentation - extensive external knowledge with video as foundation",
            10: "Maximum augmentation - comprehensive resource using video as starting point"
        }
    
    def prep(self):
        """
        Prepare for execution by reading necessary data from shared memory.
        
        Reads:
        - recommended_rubrics: list of dicts with rubric details
        """
        logger.info("Reading recommended rubrics from shared memory")
        
        # Check if required data exists in shared memory
        if "recommended_rubrics" not in self.shared_memory or not self.shared_memory["recommended_rubrics"]:
            error_msg = "Recommended rubrics not found in shared memory or recommendations list is empty"
            logger.error(error_msg)
            self.shared_memory["error"] = error_msg
            return
            
        self.recommended_rubrics = self.shared_memory["recommended_rubrics"]
        logger.debug(f"Found {len(self.recommended_rubrics)} rubric recommendations")
    
    def exec(self):
        """
        Execute the node's main functionality.
        
        Presents options to the user and captures selection.
        """
        logger.info("Presenting rubric options to user")
        
        try:
            # Display recommendations to the user
            print("\n=== Recommended Transformation Rubrics ===")
            for i, rubric in enumerate(self.recommended_rubrics, 1):
                print(f"{i}. {rubric['name']} (Confidence: {rubric['confidence']}%)")
                print(f"   Description: {rubric['description']}")
                print(f"   Justification: {rubric['justification']}")
                print(f"   Default Knowledge Level: {rubric.get('knowledge_level', 5)}/10")
                print()
            
            # Get user selection
            selection = None
            while selection is None:
                try:
                    user_input = input("Select a rubric number (or enter 'q' to quit): ")
                    
                    if user_input.lower() == 'q':
                        error_msg = "User cancelled rubric selection"
                        logger.info(error_msg)
                        self.shared_memory["error"] = error_msg
                        return
                    
                    selection_index = int(user_input) - 1
                    if 0 <= selection_index < len(self.recommended_rubrics):
                        selection = self.recommended_rubrics[selection_index]
                        logger.info(f"User selected rubric: {selection['name']}")
                    else:
                        print(f"Please enter a number between 1 and {len(self.recommended_rubrics)}")
                except ValueError:
                    print("Please enter a valid number")
            
            self.selected_rubric = selection
            
            # Get knowledge level selection
            print("\n=== Knowledge Augmentation Level Selection ===")
            print("Control how much external knowledge is incorporated into the transformation:")
            
            # Show the current default knowledge level
            default_knowledge_level = self.selected_rubric.get('knowledge_level', 5)
            print(f"Current level: {default_knowledge_level}/10 - {self.knowledge_level_descriptions[default_knowledge_level]}")
            
            # Show all knowledge level options
            print("\nKnowledge Level Options:")
            for level, description in self.knowledge_level_descriptions.items():
                print(f"{level}: {description}")
            
            knowledge_level = None
            while knowledge_level is None:
                try:
                    user_input = input(f"\nSelect knowledge level (1-10) [Default: {default_knowledge_level}]: ")
                    
                    if not user_input.strip():
                        knowledge_level = default_knowledge_level
                        logger.info(f"User selected default knowledge level: {knowledge_level}")
                    else:
                        level = int(user_input)
                        if 1 <= level <= 10:
                            knowledge_level = level
                            logger.info(f"User selected knowledge level: {knowledge_level}")
                        else:
                            print("Please enter a number between 1 and 10")
                except ValueError:
                    print("Please enter a valid number")
            
            # Update the selected rubric with the chosen knowledge level
            self.selected_rubric['knowledge_level'] = knowledge_level
            
            # Get audience level selection
            print("\n=== Audience Level Selection ===")
            for i, (level, desc) in enumerate(self.audience_levels.items(), 1):
                print(f"{i}. {level.capitalize()}: {desc}")
                print()
            
            audience_selection = None
            while audience_selection is None:
                try:
                    user_input = input(f"Select an audience level (1-{len(self.audience_levels)}) [Default: Sophisticated]: ")
                    
                    if not user_input.strip():
                        audience_selection = self.default_audience
                        logger.info(f"User selected default audience level: {audience_selection}")
                    else:
                        audience_index = int(user_input) - 1
                        audience_keys = list(self.audience_levels.keys())
                        if 0 <= audience_index < len(audience_keys):
                            audience_selection = audience_keys[audience_index]
                            logger.info(f"User selected audience level: {audience_selection}")
                        else:
                            print(f"Please enter a number between 1 and {len(self.audience_levels)}")
                except ValueError:
                    print("Please enter a valid number")
            
            self.audience_level = audience_selection
            
        except Exception as e:
            error_msg = f"Error in rubric selection: {str(e)}"
            logger.exception(error_msg)
            self.shared_memory["error"] = error_msg
    
    def post(self):
        """
        Post-process and write results to shared memory.
        
        Writes:
        - selected_rubric: dict with rubric details
        - audience_level: str representing selected audience level
        """
        logger.info("Writing selected rubric and audience level to shared memory")
        
        # Write selected rubric and audience level to shared memory
        self.shared_memory["selected_rubric"] = self.selected_rubric
        self.shared_memory["audience_level"] = self.audience_level
        
        # Make sure knowledge level is stored as a top-level key in shared memory
        self.shared_memory["knowledge_level"] = self.selected_rubric.get("knowledge_level", 5)
        logger.info(f"Knowledge level {self.shared_memory['knowledge_level']} saved to shared memory")
        
        # Log completion
        logger.info(f"Rubric selection completed: {self.selected_rubric['name']}, Knowledge Level: {self.selected_rubric.get('knowledge_level', 5)}/10, Audience: {self.audience_level}")
