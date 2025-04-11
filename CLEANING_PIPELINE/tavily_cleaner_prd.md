# Product Requirements Document: Tavily Results Cleaner

## 1. Overview

### 1.1 Purpose
The Tavily Results Cleaner is a Python module designed to process and clean raw Tavily search results, particularly focusing on news content. It transforms large, messy HTML content into clean, structured text suitable for further processing by LLMs or other pipeline components.

### 1.2 Problem Statement
Tavily's advanced search API returns results that can include large raw HTML content (sometimes 700K+ characters), often containing multiple articles, navigation elements, advertisements, and other noise. This creates challenges:
- Content is too large to efficiently process with LLMs
- Text includes irrelevant material not related to the main article
- Content formatting is inconsistent across websites
- News aggregator sites combine multiple stories into a single page
- Some results may not include raw_content, requiring fallback to content snippets

### 1.3 Goals
- Create a standalone module that efficiently cleans and structures Tavily search results
- Reduce content size by 80-95% while preserving the most relevant information
- Handle various types of news sources (dedicated articles, aggregator sites)
- Maintain a consistent output structure regardless of input variations
- Provide fallback mechanisms when raw_content is not available

### 1.4 Non-Goals
- This module will not perform analysis or summarization of the content (leaving that to LLMs)
- It will not extract sentiment, entities, or other semantic information
- It will not crawl additional URLs or fetch more content than provided in the Tavily results
- It will not restructure or modify the overall Tavily response format, only clean specific fields

## 2. User Experience

### 2.1 User Types
- Data Engineers: Integrating this module into data pipelines
- AI Engineers: Using this module to prepare content for LLM processing
- Researchers: Analyzing news content programmatically

### 2.2 User Journey
1. User obtains raw Tavily search results JSON from an API call or file
2. User passes the results to the cleaner module
3. Module processes and returns cleaned, structured results
4. User proceeds with further analysis or LLM processing with the cleaned data

## 3. Functional Requirements

### 3.1 Core Functionality

#### 3.1.1 Content Extraction and Cleaning
- **RF-1**: Extract main article content from raw HTML
- **RF-2**: Remove navigation elements, advertisements, and other non-article content
- **RF-3**: Preserve important formatting elements (paragraphs, lists, headings)
- **RF-4**: Set reasonable limits on content length (configurable)
- **RF-5**: Handle various HTML structures from different news sites

#### 3.1.2 Content Truncation and Boundary Detection
- **RF-6**: Detect article boundaries within aggregator pages
- **RF-7**: Prioritize extraction of the main/first article when multiple are present
- **RF-8**: Provide metadata about truncation when it occurs
- **RF-9**: Implement configurable truncation strategies

#### 3.1.3 Fallback Mechanisms
- **RF-10**: Use content field when raw_content is not available
- **RF-11**: Attempt URL fetching as secondary fallback (optional, configurable)
- **RF-12**: Provide clear indicators when fallbacks are used

#### 3.1.4 Metadata Enhancement
- **RF-13**: Extract and normalize publication date information
- **RF-14**: Extract author information when available
- **RF-15**: Identify content type (news article, blog post, etc.)
- **RF-16**: Extract image captions and incorporate into text where relevant

### 3.2 Input Processing
- **RF-17**: Accept complete Tavily results JSON as input
- **RF-18**: Support processing of individual result items
- **RF-19**: Handle malformed or unexpected input gracefully
- **RF-20**: Support batch processing of multiple results

### 3.3 Output Format
- **RF-21**: Maintain the original Tavily response structure
- **RF-22**: Add a new field `cleaned_content` to each result item
- **RF-23**: Include extraction metadata (strategy used, truncation info)
- **RF-24**: Support multiple output formats (JSON, dict, custom object)

## 4. Technical Requirements

### 4.1 Dependencies
- **RT-1**: Minimize external dependencies to essential libraries
- **RT-2**: Required libraries:
  - `newspaper3k` for article extraction
  - `trafilatura` as fallback extractor
  - `beautifulsoup4` for HTML parsing
  - Standard libraries (json, re, typing, etc.)

### 4.2 Performance
- **RT-3**: Process a typical Tavily result (5 items) in under 5 seconds
- **RT-4**: Support parallel processing for batch operations
- **RT-5**: Memory efficient handling of large HTML content

### 4.3 Error Handling
- **RT-6**: Graceful handling of malformed HTML
- **RT-7**: Fallback chain when primary extraction fails
- **RT-8**: Detailed logging of extraction attempts and failures
- **RT-9**: Never fail catastrophically - always return a valid result structure

### 4.4 Configurability
- **RT-10**: Configurable extraction strategies
- **RT-11**: Adjustable content length limits
- **RT-12**: Enable/disable specific features (metadata extraction, fallbacks)
- **RT-13**: Custom extraction rules for known problematic sites

## 5. Architecture

### 5.1 Module Structure
```
src/utils/tavily_cleaner/
├── __init__.py
├── cleaner.py          # Main entry point
├── extractors/         # Content extraction strategies
│   ├── __init__.py
│   ├── newspaper.py    # newspaper3k implementation
│   ├── trafilatura.py  # trafilatura implementation
│   ├── fallback.py     # Simple regex fallbacks
│   └── factory.py      # Strategy selection
├── processors/         # Content post-processing
│   ├── __init__.py
│   ├── truncator.py    # Content truncation logic
│   ├── boundary.py     # Article boundary detection
│   └── metadata.py     # Metadata extraction
└── models/             # Data models
    ├── __init__.py
    ├── input.py        # Input validators
    └── output.py       # Output formatters
```

### 5.2 Process Flow
1. **Input Validation**: Verify Tavily result structure
2. **Extraction Strategy Selection**: Choose appropriate extractor based on URL and content
3. **Content Extraction**: Extract main content using selected strategy
4. **Boundary Detection**: Identify article boundaries (for aggregator sites)
5. **Truncation**: Apply length limits and truncation if needed
6. **Metadata Enhancement**: Extract and add additional metadata
7. **Output Formatting**: Structure the cleaned results

### 5.3 Integration Points
- **Direct function calls**: `clean_tavily_results(results_json)`
- **Stream processing**: `TavilyCleanerPipeline` for integration into data pipelines
- **CLI interface**: For standalone testing and manual cleaning

## 6. Testing and Validation

### 6.1 Test Cases
- **TC-1**: Various news sources (CNN, BBC, Reuters, etc.)
- **TC-2**: Aggregator sites (Google News, Yahoo News)
- **TC-3**: Blog posts and opinion pieces
- **TC-4**: Malformed HTML content
- **TC-5**: Missing raw_content field
- **TC-6**: Edge cases (minimal content, paywall content)

### 6.2 Quality Metrics
- **QM-1**: Content relevance (manual validation)
- **QM-2**: Noise reduction percentage
- **QM-3**: Processing time
- **QM-4**: Success rate across diverse sources

## 7. Implementation Plan

### 7.1 Phase 1: Core Functionality
- Basic extraction using newspaper3k
- Simple content truncation
- Input/output structure

### 7.2 Phase 2: Enhanced Extraction
- Multiple extraction strategies
- Boundary detection
- Metadata enhancement

### 7.3 Phase 3: Refinement and Optimization
- Performance optimization
- Site-specific extraction rules
- Advanced configuration options

## 8. Success Criteria
- Successfully process 95%+ of Tavily news search results
- Reduce content size by at least 80% while preserving key information
- Process 5 results in under 5 seconds
- Zero catastrophic failures (always return usable output)
- Clear identification of article boundaries in aggregator sites

## 9. Open Questions and Concerns
- How to handle paywalled content?
- Should we implement website-specific extraction rules for major news sites?
- Is there value in attempting to extract structured data (tables, lists) in special formats?
- Should we implement URL fetching as a fallback, or is that outside the scope?

## 10. Appendix

### 10.1 Sample Input/Output

**Input:**
```json
{
  "query": "latest Ukraine war news",
  "results": [
    {
      "title": "Russia-Ukraine war latest news",
      "url": "https://example.com/news/ukraine-war",
      "content": "Short content snippet",
      "score": 0.92,
      "raw_content": "<html>...700KB of messy HTML...</html>"
    }
  ]
}
```

**Output:**
```json
{
  "query": "latest Ukraine war news",
  "results": [
    {
      "title": "Russia-Ukraine war latest news",
      "url": "https://example.com/news/ukraine-war",
      "content": "Short content snippet",
      "score": 0.92,
      "raw_content": "<html>...700KB of messy HTML...</html>",
      "cleaned_content": "Russia has launched new offensive operations in eastern Ukraine. Ukrainian forces report heavy fighting near Kharkiv. The United States announced a new $1.4 billion military aid package.",
      "extraction_metadata": {
        "strategy": "newspaper3k",
        "truncated": true,
        "original_length": 723456,
        "cleaned_length": 5421,
        "publication_date": "2025-04-10",
        "content_type": "news_article"
      }
    }
  ],
  "processing_metadata": {
    "processed_at": "2025-04-11T15:30:00Z",
    "version": "1.0.0",
    "processing_time_ms": 1200
  }
}
```
