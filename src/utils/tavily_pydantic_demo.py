from typing import Optional, Any, Union, List, Dict
from pydantic import BaseModel, Field, SkipValidation, model_validator
from pydantic_ai import Agent, RunContext, Tool
from tavily import TavilyClient
from google import genai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import logfire

# configure logfire
logfire.configure(token=os.getenv('LOGFIRE_WRITE_TOKEN'))
# Instrument pydantic-ai
logfire.instrument_pydantic_ai()


class TavilySearchInput(BaseModel):
    query: str = Field(..., description="Search query to find information")
    search_depth: str = Field("basic", description="Search depth - 'basic' or 'advanced'")
    use_gemini: bool = Field(False, description="Whether to use Gemini to process results")

class SearchResultItem(BaseModel):
    title: str
    content: str
    url: str
    metadata: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of a search result item"""
        return f"Title: {self.title}\nURL: {self.url}\nMetadata: {self.metadata or 'None'}"
    
    def as_markdown(self) -> str:
        """Return the result as markdown formatted text"""
        return f"### {self.title}\n**URL**: {self.url}\n**Metadata**: {self.metadata or 'None'}\n\n{self.content}"
    
class TavilyGeminiOutput(BaseModel):
    search_query: str
    result_items: List[SearchResultItem]
    summary: str
    
    @model_validator(mode="after")
    def validate_data(self) -> "TavilyGeminiOutput":
        """Ensure that there's at least a summary even if empty result items"""
        if not self.result_items and not self.summary:
            self.summary = "No results found for this query."
        return self
    
    def as_dict(self) -> Dict:
        """Convert to dictionary with nested models also converted"""
        return {
            "search_query": self.search_query,
            "result_items": [item.model_dump() for item in self.result_items],
            "summary": self.summary
        }
    
    def as_markdown(self) -> str:
        """Return the results as markdown formatted text"""
        md = f"# Search Results: {self.search_query}\n\n"
        md += f"## Summary\n{self.summary}\n\n"
        md += "## Result Items\n\n"
        for i, item in enumerate(self.result_items, 1):
            md += f"{i}. {item.as_markdown()}\n\n"
        return md

class SearchResult(BaseModel):
    query: str
    results: list[dict]
    answer: Optional[str] = None
    gemini_analysis: Optional[str] = None

class TavilyDependencies(BaseModel):
    tavily_client: TavilyClient
    gemini_client: Optional[SkipValidation[Any]] = None

    model_config = {
        "arbitrary_types_allowed": True
    }

# Initialize Gemini if API key exists
if os.getenv('GEMINI_API_KEY'):
    gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
else:
    gemini_client = None

# Create the agent
search_agent = Agent[TavilyDependencies, SearchResult](
    system_prompt="""You are a research assistant that uses Tavily to search for information.
    When given a query, use the search tool to find relevant information.
    
    IMPORTANT GUIDELINES:
    1. Return the RAW search results exactly as provided by the Tavily search tool.
    2. Do NOT summarize, interpret, or modify the search results in any way.
    3. Do NOT add any commentary, analysis, or additional information.
    4. Simply pass through the exact information returned by the search tool.
    5. If the search returns multiple results, include all of them without filtering.
    """,
    model="google-gla:gemini-2.5-pro-exp-03-25"
)

@search_agent.tool
async def tavily_search(
    ctx: RunContext[TavilyDependencies],
    query: str,
    search_depth: str = "advanced",
    use_gemini: bool = False
) -> SearchResult:
    """
    Search for information using Tavily API.
    Returns search results and an optional answer if available.
    """
    # Perform the search
    search_response = ctx.deps.tavily_client.search(
        query=query,
        search_depth="advanced"
    )
    
    # Try to get a quick answer if available
    try:
        answer = ctx.deps.tavily_client.qna_search(query=query)
    except:
        answer = None
    
    # We're not using this method for Gemini analysis anymore
    # Instead, we're using a separate agent with result_type=TavilyGeminiOutput
    gemini_analysis = None

    return SearchResult(
        query=query,
        results=search_response.get('results', []),
        answer=answer,
        gemini_analysis=gemini_analysis
    )

async def search_with_tavily(query: str, use_gemini: bool = False) -> Union[SearchResult, TavilyGeminiOutput]:
    """
    Main function to execute a search using the agent.
    """
    # Initialize clients
    tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
    deps = TavilyDependencies(
        tavily_client=tavily_client,
        gemini_client=gemini_client if use_gemini else None
    )
    
    if use_gemini:
        # Create a Gemini-enhanced agent with structured output format
        try:
            # Using a structured output model
            gemini_agent = Agent[TavilyDependencies, TavilyGeminiOutput](
                system_prompt="""You are a research assistant that uses Tavily to search for information.
                When given a query, analyze the search results and format your response according to the specified structure.
                
                VERY IMPORTANT: You MUST format your final response according to the TavilyGeminiOutput schema with these exact fields:
                1. search_query - The original search query
                2. result_items - An array of items, each with title, content, url, and metadata fields
                3. summary - A comprehensive but concise summary of all results
                
                For each result item:
                - Extract the raw facts without interpretation
                - Include relevant metadata such as dates, sources, and publications
                - Preserve the original content structure
                - Remove duplicate information
                
                For the summary field:
                - Provide a comprehensive but concise summary of all the results
                - Highlight key points and trends across sources
                
                Remember: Your final response MUST conform exactly to the expected structure.
                """,
                model="google-gla:gemini-2.5-pro-exp-03-25",  # Using Gemini model as requested
                result_type=TavilyGeminiOutput
            )
        except Exception as e:
            print(f"Error creating structured output agent: {e}")
            # If we can't create the agent, return a basic result
            return SearchResult(
                query=query,
                results=[],
                answer=f"Error creating structured agent: {e}"
            )
        
        # Register the tavily_search tool with the gemini_agent
        @gemini_agent.tool
        async def gemini_tavily_search(
            ctx: RunContext[TavilyDependencies],
            query: str,
            search_depth: str = "advanced"
        ) -> dict:
            """
            Search for information using Tavily API and format the results for structured output.
            You'll need to format these results according to the TavilyGeminiOutput schema with fields:
            - search_query: The original query string
            - result_items: Array of items each with title, content, url, and metadata
            - summary: A concise summary of all results
            """
            # Perform the search
            search_response = ctx.deps.tavily_client.search(
                query=query,
                search_depth="advanced"
            )
            
            # Try to get a quick answer if available
            try:
                answer = ctx.deps.tavily_client.qna_search(query=query)
            except:
                answer = None
            
            # Format the data to make it easier for the model to understand the structure    
            formatted_results = []
            for result in search_response.get('results', []):
                formatted_results.append({
                    "title": result.get('title', 'No title'),
                    "content": result.get('content', 'No content'),
                    "url": result.get('url', 'No URL'),
                    "metadata": f"Score: {result.get('score', 'N/A')}"
                })
                
            return {
                "original_query": query,
                "formatted_results": formatted_results,
                "quick_answer": answer,
                "result_count": len(formatted_results),
                "structure_note": "Format your response according to TavilyGeminiOutput with search_query, result_items, and summary fields"
            }
        
        try:
            # Run the Gemini agent with structured output
            result = await gemini_agent.run(
                f"Search for and analyze: {query}",
                deps=deps
            )
            return result.data
        except Exception as e:
            print(f"Error with structured output agent: {e}")
            # Fall back to standard agent with manual processing
            result = await search_agent.run(
                f"Search for: {query}",
                deps=deps
            )
            
            # Process the results manually to create a TavilyGeminiOutput
            if hasattr(result, 'data') and isinstance(result.data, SearchResult):
                search_data = result.data
                
                # Create result items from search results
                result_items = []
                for res in search_data.results:
                    result_items.append(SearchResultItem(
                        title=res.get('title', 'No title'),
                        content=res.get('content', 'No content'),
                        url=res.get('url', 'No URL'),
                        metadata=None
                    ))
                
                # Create a simple summary
                summary = search_data.answer if search_data.answer else "No summary available"
                
                # Return structured output
                return TavilyGeminiOutput(
                    search_query=query,
                    result_items=result_items,
                    summary=summary
                )
            else:
                # If we can't get structured data, return a basic result
                return SearchResult(
                    query=query,
                    results=[],
                    answer=str(result) if result else None
                )
        except Exception as e:
            print(f"Error with fallback processing: {e}")
            # If all else fails, return a basic result
            return SearchResult(
                query=query,
                results=[],
                answer=f"Error processing search: {e}"
            )
    else:
        # Run the standard agent for raw results
        result = await search_agent.run(
            f"Search for: {query}",
            deps=deps
        )
        # Check if result is a string or has a data attribute
        if hasattr(result, 'data'):
            return result.data
        else:
            # Create a SearchResult object with the available information
            return SearchResult(
                query=query,
                results=[],
                answer=str(result) if result else None
            )

# ======== Pydantic Model Demonstration Functions ========

def demonstrate_pydantic_model(model: TavilyGeminiOutput):
    """
    Demonstrate various ways to work with a Pydantic model
    """
    print("\n" + "="*80)
    print("PYDANTIC MODEL DEMONSTRATION")
    print("="*80)
    
    # 1. Accessing fields with dot notation
    print("\n1. Accessing fields with dot notation:")
    print(f"Search Query: {model.search_query}")
    print(f"Number of results: {len(model.result_items)}")
    print(f"First result title: {model.result_items[0].title if model.result_items else 'No results'}")
    print(f"Summary length: {len(model.summary)} characters")
    
    # 2. Model validation and transformation
    print("\n2. Model validation and transformation:")
    print(f"Model is valid: {model.model_dump_json() is not None}")
    
    # 3. Converting to dict and JSON
    print("\n3. Converting to dict and JSON:")
    model_dict = model.model_dump()
    print(f"Dict keys: {list(model_dict.keys())}")
    model_json = model.model_dump_json(indent=2)
    print(f"JSON excerpt (first 100 chars):\n{model_json[:100]}...")
    
    # 4. Custom methods
    print("\n4. Custom methods:")
    print(f"Custom as_dict method: {list(model.as_dict().keys())}")
    markdown = model.as_markdown()
    print(f"Custom markdown format (excerpt):\n{markdown[:150]}...")
    
    # 5. Using with field subset
    print("\n5. Using with model_dump to get specific fields:")
    summary_only = model.model_dump(include={"summary"})
    print(f"Summary only: {summary_only}")
    
    # 6. Model copy and update
    print("\n6. Model copy and update:")
    updated_model = model.model_copy(update={"search_query": f"{model.search_query} (updated)"})
    print(f"Updated query: {updated_model.search_query}")
    
    # 7. Serialization and deserialization
    print("\n7. Serialization and deserialization:")
    serialized = model.model_dump_json()
    deserialized = TavilyGeminiOutput.model_validate_json(serialized)
    print(f"Deserialized model is identical: {deserialized.search_query == model.search_query}")
    
    # 8. Field info and schema
    print("\n8. Field info and schema:")
    schema = TavilyGeminiOutput.model_json_schema()
    print(f"Schema properties: {list(schema.get('properties', {}).keys())}")
    
    print("\n" + "="*80)
    print("END OF PYDANTIC MODEL DEMONSTRATION")
    print("="*80 + "\n")

if __name__ == "__main__":
    import asyncio
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Search for information using Tavily API')
    parser.add_argument('query', type=str, nargs='?', default=None, help='Search query')
    parser.add_argument('--gemini', dest='use_gemini', action='store_true', help='Enable Gemini analysis')
    parser.set_defaults(use_gemini=False)
    args = parser.parse_args()
    
    # If no query is provided, prompt the user
    if args.query is None:
        args.query = input("Enter your search query: ")
    
    async def example_search():
        try:
            print(f"Running search for: '{args.query}'" + (" with Gemini analysis" if args.use_gemini else ""))
            print("\nPlease wait, this may take a moment...\n")
            
            result = await search_with_tavily(
                query=args.query,
                use_gemini=args.use_gemini
            )

            # Check result type
            if isinstance(result, str):
                print(f"Result: {result}")
            elif isinstance(result, TavilyGeminiOutput):
                print(f"Search results for: {result.search_query}")
                
                # Demonstrate Pydantic model capabilities
                demonstrate_pydantic_model(result)
                
                # Display the structured results
                if args.use_gemini and isinstance(result, TavilyGeminiOutput):
                    print(f"\n=== GEMINI STRUCTURED ANALYSIS ===\n")
                    
                    # Display in a structured format
                    print(f"QUERY: {result.search_query}\n")
                    
                    print("SEARCH RESULTS:")
                    for i, item in enumerate(result.result_items, 1):
                        print(f"\n[{i}] {item.title}")
                        if item.metadata:
                            print(f"METADATA: {item.metadata}")
                        print(f"URL: {item.url}")
                        print(f"CONTENT: {item.content}")
                    
                    print(f"\nSUMMARY:\n{result.summary}")
                    print(f"\n=== END GEMINI ANALYSIS ===\n")
            else:
                print(f"Search results for: {result.query}")
                
                if args.use_gemini and result.gemini_analysis:
                    print(f"\n=== GEMINI STRUCTURED ANALYSIS ===\n")
                    print(result.gemini_analysis)
                    print(f"\n=== END GEMINI ANALYSIS ===\n")
                else:
                    # Display raw search results
                    if result.answer:
                        print(f"\nQuick answer: {result.answer}")
                    
                    print(f"\nFound {len(result.results)} results:")
                    for i, res in enumerate(result.results, 1):
                        print(f"\n[{i}] {res.get('title', 'No title')}")
                        print(f"URL: {res.get('url', 'No URL')}")
                        print(f"Content: {res.get('content', 'No content')}")
        except Exception as e:
            print(f"Error during search: {e}")

    asyncio.run(example_search())
