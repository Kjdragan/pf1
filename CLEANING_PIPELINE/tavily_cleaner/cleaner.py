"""
Main cleaner module for Tavily Results Cleaner.

This module provides the main entry points for cleaning Tavily search results
using the PocketFlow approach.
"""

import json
import time
from typing import Dict, Any, Union, List, Optional
import asyncio
import copy

from .models.input import validate_tavily_results, TavilyResult
from .models.output import CleanedTavilyResult, CleanedTavilyResults, ExtractionMetadata
from .extractors.factory import get_extractor
from .processors.truncator import truncate_content
from .processors.boundary import detect_article_boundaries
from .processors.metadata import extract_metadata


# Import PocketFlow classes
class BaseNode:
    def __init__(self): self.params,self.successors={},{}
    def set_params(self,params): self.params=params
    def next(self,node,action="default"):
        if action in self.successors: import warnings; warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action]=node; return node
    def prep(self,shared): pass
    def exec(self,prep_res): pass
    def post(self,shared,prep_res,exec_res): pass
    def _exec(self,prep_res): return self.exec(prep_res)
    def _run(self,shared): p=self.prep(shared); e=self._exec(p); return self.post(shared,p,e)
    def run(self,shared): 
        if self.successors: import warnings; warnings.warn("Node won't run successors. Use Flow.")  
        return self._run(shared)
    def __rshift__(self,other): return self.next(other)
    def __sub__(self,action):
        if isinstance(action,str): return _ConditionalTransition(self,action)
        raise TypeError("Action must be a string")

class _ConditionalTransition:
    def __init__(self,src,action): self.src,self.action=src,action
    def __rshift__(self,tgt): return self.src.next(tgt,self.action)

class Node(BaseNode):
    def __init__(self,max_retries=1,wait=0): super().__init__(); self.max_retries,self.wait=max_retries,wait
    def exec_fallback(self,prep_res,exc): raise exc
    def _exec(self,prep_res):
        for self.cur_retry in range(self.max_retries):
            try: return self.exec(prep_res)
            except Exception as e:
                if self.cur_retry==self.max_retries-1: return self.exec_fallback(prep_res,e)
                if self.wait>0: import time; time.sleep(self.wait)

class BatchNode(Node):
    def _exec(self,items): return [super(BatchNode,self)._exec(i) for i in (items or [])]

class Flow(BaseNode):
    def __init__(self,start=None): super().__init__(); self.start_node=start
    def start(self,start): self.start_node=start; return start
    def get_next_node(self,curr,action):
        nxt=curr.successors.get(action or "default")
        if not nxt and curr.successors: import warnings; warnings.warn(f"Flow ends: '{action}' not found in {list(curr.successors)}")
        return nxt
    def _orch(self,shared,params=None):
        curr,p,last_action =copy.copy(self.start_node),(params or {**self.params}),None
        while curr: curr.set_params(p); last_action=curr._run(shared); curr=copy.copy(self.get_next_node(curr,last_action))
        return last_action
    def _run(self,shared): p=self.prep(shared); o=self._orch(shared); return self.post(shared,p,o)
    def post(self,shared,prep_res,exec_res): return exec_res


# Define the nodes for our cleaning pipeline
class ValidateInputNode(Node):
    """Node for validating Tavily search results input."""
    
    def prep(self, shared):
        """Prepare the input for validation."""
        return shared.get('input_data')
    
    def exec(self, input_data):
        """Validate the input data."""
        try:
            # Validate the input data
            validated_data = validate_tavily_results(input_data)
            return validated_data
        except ValueError as e:
            # Handle validation errors
            return {'error': str(e)}
    
    def post(self, shared, input_data, validated_data):
        """Store the validated data in the shared context."""
        if 'error' in validated_data:
            shared['error'] = validated_data['error']
            return 'error'
        
        shared['validated_data'] = validated_data
        return 'default'


class ExtractResultsNode(Node):
    """Node for extracting individual results from Tavily search results."""
    
    def prep(self, shared):
        """Prepare the validated data for extraction."""
        return shared.get('validated_data')
    
    def exec(self, validated_data):
        """Extract individual results from the validated data."""
        query = validated_data.get('query', '')
        results = validated_data.get('results', [])
        
        # Convert results to TavilyResult objects
        tavily_results = [TavilyResult.from_dict(result) for result in results]
        
        return {
            'query': query,
            'results': tavily_results,
            'answer': validated_data.get('answer'),
            'response_time': validated_data.get('response_time')
        }
    
    def post(self, shared, validated_data, extracted_data):
        """Store the extracted data in the shared context."""
        shared['extracted_data'] = extracted_data
        return 'default'


class CleanResultsBatchNode(BatchNode):
    """Node for cleaning a batch of Tavily search results."""
    
    def prep(self, shared):
        """Prepare the results for cleaning."""
        extracted_data = shared.get('extracted_data', {})
        return extracted_data.get('results', [])
    
    def exec(self, result):
        """Clean an individual result."""
        if not isinstance(result, TavilyResult):
            return {'error': 'Invalid result object'}
        
        start_time = time.time()
        
        # Get the appropriate extractor for this URL
        extractor = get_extractor(result.url, result.raw_content)
        
        # Extract content if raw_content is available
        if result.has_raw_content():
            extraction_result = extractor.extract(result.raw_content, result.url)
            
            # Use the extracted content if successful, otherwise use the original content
            if extraction_result.get('success', False):
                content = extraction_result.get('content', '')
                
                # Detect article boundaries
                boundary_result = detect_article_boundaries(content)
                
                # Use the main article if multiple articles were detected
                if boundary_result.get('is_aggregator', False):
                    content = boundary_result.get('main_article', content)
                
                # Truncate content if needed
                truncation_result = truncate_content(content)
                content = truncation_result.get('content', '')
                
                # Extract additional metadata
                metadata = extract_metadata(
                    content, 
                    result.url, 
                    {
                        'date': extraction_result.get('date'),
                        'author': extraction_result.get('author')
                    }
                )
                
                # Create extraction metadata
                extraction_metadata = ExtractionMetadata(
                    strategy=extractor.name,
                    truncated=truncation_result.get('truncated', False),
                    original_length=truncation_result.get('original_length', 0),
                    cleaned_length=truncation_result.get('truncated_length', 0),
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    publication_date=metadata.get('date'),
                    author=metadata.get('author'),
                    content_type=metadata.get('content_type', 'unknown')
                )
                
                # Create cleaned result
                cleaned_result = CleanedTavilyResult(
                    title=result.title,
                    url=result.url,
                    content=result.content,
                    score=result.score,
                    cleaned_content=content,
                    extraction_metadata=extraction_metadata,
                    raw_content=None  # Don't include raw_content in output to save space
                )
                
                return cleaned_result
        
        # If raw_content is not available or extraction failed, use the original content
        # Create extraction metadata for fallback
        extraction_metadata = ExtractionMetadata(
            strategy='content_fallback',
            truncated=False,
            original_length=len(result.content),
            cleaned_length=len(result.content),
            processing_time_ms=int((time.time() - start_time) * 1000),
            content_type='snippet'
        )
        
        # Create cleaned result with original content
        cleaned_result = CleanedTavilyResult(
            title=result.title,
            url=result.url,
            content=result.content,
            score=result.score,
            cleaned_content=result.content,  # Use original content as cleaned content
            extraction_metadata=extraction_metadata,
            raw_content=None
        )
        
        return cleaned_result
    
    def post(self, shared, results, cleaned_results):
        """Store the cleaned results in the shared context."""
        shared['cleaned_results'] = cleaned_results
        return 'default'


class AssembleOutputNode(Node):
    """Node for assembling the final cleaned output."""
    
    def prep(self, shared):
        """Prepare the data for output assembly."""
        return {
            'extracted_data': shared.get('extracted_data', {}),
            'cleaned_results': shared.get('cleaned_results', [])
        }
    
    def exec(self, data):
        """Assemble the final output."""
        extracted_data = data.get('extracted_data', {})
        cleaned_results = data.get('cleaned_results', [])
        
        # Create the final output
        output = CleanedTavilyResults(
            query=extracted_data.get('query', ''),
            results=cleaned_results,
            answer=extracted_data.get('answer'),
            response_time=extracted_data.get('response_time')
        )
        
        return output
    
    def post(self, shared, data, output):
        """Store the final output in the shared context."""
        shared['output'] = output
        return 'default'


class FormatOutputNode(Node):
    """Node for formatting the output as requested."""
    
    def prep(self, shared):
        """Prepare the output for formatting."""
        return {
            'output': shared.get('output'),
            'output_format': shared.get('output_format', 'dict')
        }
    
    def exec(self, data):
        """Format the output as requested."""
        output = data.get('output')
        output_format = data.get('output_format', 'dict')
        
        if not output:
            return {'error': 'No output to format'}
        
        if output_format == 'json':
            # Convert to JSON string
            return json.dumps(output.to_dict(), indent=2)
        elif output_format == 'dict':
            # Convert to dictionary
            return output.to_dict()
        else:
            # Return the object as is
            return output
    
    def post(self, shared, data, formatted_output):
        """Store the formatted output in the shared context."""
        shared['formatted_output'] = formatted_output
        return 'default'


# Create the cleaning flow
def create_cleaning_flow() -> Flow:
    """Create the flow for cleaning Tavily search results."""
    flow = Flow()
    
    # Define the nodes
    validate_node = ValidateInputNode()
    extract_node = ExtractResultsNode()
    clean_node = CleanResultsBatchNode()
    assemble_node = AssembleOutputNode()
    format_node = FormatOutputNode()
    
    # Connect the nodes
    flow.start(validate_node)
    validate_node.next(extract_node)
    extract_node.next(clean_node)
    clean_node.next(assemble_node)
    assemble_node.next(format_node)
    
    # Add error handling
    validate_node - 'error' >> Node()  # Terminal node for validation errors
    
    return flow


# Main entry point functions
def clean_tavily_results(
    results: Union[Dict[str, Any], str], 
    output_format: str = 'dict'
) -> Union[Dict[str, Any], str, CleanedTavilyResults]:
    """
    Clean Tavily search results.
    
    Args:
        results: Tavily search results as a dictionary or JSON string
        output_format: Output format ('dict', 'json', or 'object')
        
    Returns:
        Cleaned Tavily search results in the requested format
    """
    # Create the shared context
    shared = {
        'input_data': results,
        'output_format': output_format
    }
    
    # Create and run the flow
    flow = create_cleaning_flow()
    flow.run(shared)
    
    # Return the formatted output
    if 'error' in shared:
        return {'error': shared['error']}
    
    return shared.get('formatted_output')


def clean_result_item(
    result: Dict[str, Any], 
    output_format: str = 'dict'
) -> Union[Dict[str, Any], str, CleanedTavilyResult]:
    """
    Clean a single Tavily search result item.
    
    Args:
        result: A single Tavily search result item
        output_format: Output format ('dict', 'json', or 'object')
        
    Returns:
        Cleaned Tavily search result item in the requested format
    """
    # Convert to TavilyResult
    tavily_result = TavilyResult.from_dict(result)
    
    # Create a CleanResultsBatchNode and run it
    clean_node = CleanResultsBatchNode()
    cleaned_result = clean_node.exec(tavily_result)
    
    # Format the output
    if output_format == 'json':
        return json.dumps(cleaned_result.to_dict(), indent=2)
    elif output_format == 'dict':
        return cleaned_result.to_dict()
    else:
        return cleaned_result
