# YouTube Video Summarizer Requirements

## Project Overview
This project creates a tool that summarizes YouTube videos in a child-friendly manner, extracts key topics, and generates Q&A pairs for each topic. The summary is presented in an HTML format.

## Core Requirements

1. **Input Processing**
   - Accept a YouTube video URL as input
   - Validate the URL to ensure it's a valid YouTube link

2. **Video Content Extraction**
   - Extract video metadata (title, channel, duration, etc.)
   - Extract audio/transcript from the video
   - Handle videos with or without captions

3. **Content Analysis**
   - Identify main topics and subtopics in the video
   - Extract key points for each topic
   - Generate relevant questions and answers for each topic
   - Ensure content is explained in a child-friendly manner (ELI5 - Explain Like I'm 5)

4. **Output Generation**
   - Generate a structured summary of the video
   - Create an HTML page to visualize the summary
   - Include video metadata, topics, and Q&A sections
   - Ensure the HTML is responsive and user-friendly

## User Experience Requirements
- Simple interface for inputting YouTube URLs
- Clear, visually appealing presentation of summaries
- Child-friendly language and explanations
- Fast processing time

## Technical Constraints
- Must work with public YouTube videos
- Should handle videos of various lengths
- Must comply with YouTube's terms of service
- Should be resilient to different video formats and content types
