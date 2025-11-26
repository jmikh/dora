#!/usr/bin/env python3
"""
Test the insight extraction prompt with a sample thread and make an OpenAI API call
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from models import RedditContent, get_session
from typing import List

# Load environment variables from .env file
load_dotenv()


def get_thread_path(comment_id: str, session) -> List[RedditContent]:
    """Get the full path from root post to a specific comment"""
    path = []
    current_id = comment_id

    while current_id:
        content = session.query(RedditContent).filter(
            RedditContent.id == current_id
        ).first()

        if not content:
            break

        path.insert(0, content)

        if content.content_type == 'comment':
            current_id = content.parent_id
        else:
            break

    return path


def format_thread_for_prompt(thread_path: List[RedditContent]) -> str:
    """Format a thread in the format expected by the prompt"""
    output = "**THREAD CONTEXT:**\n\n```\n"

    for i, item in enumerate(thread_path[:-1]):  # All except last
        prefix = "    " * i

        if item.content_type == 'post':
            output += f"{prefix}[POST - ROOT]\n"
            if item.title:
                output += f"{prefix}Title: {item.title}\n"
            if item.body:
                body = item.body[:300] + "..." if len(item.body) > 300 else item.body
                output += f"{prefix}Body: {body}\n"
        else:
            output += f"\n{prefix}[COMMENT - CONTEXT]\n"
            if item.body:
                output += f"{prefix}{item.body}\n"

    output += "```\n\n"
    output += "**TARGET COMMENT:**\n\n```\n"

    # Add target comment
    target = thread_path[-1]
    if target.body:
        output += target.body + "\n"

    output += "```"

    return output


def test_prompt():
    """Test the prompt with a sample thread and call OpenAI API"""
    session = get_session()

    # Get a comment with good depth and content
    # Let's use one of the examples we found
    comment_id = "t1_nk96nwy" 

    thread_path = get_thread_path(comment_id, session)

    if not thread_path:
        print("Thread not found!")
        return

    print("=" * 80)
    print("TEST INSIGHT EXTRACTION PROMPT (Comment Thread)")
    print("=" * 80)
    print(f"\nComment ID: {comment_id}")
    print(f"Thread depth: {len(thread_path)} levels\n")

    # Format the thread
    formatted_thread = format_thread_for_prompt(thread_path)

    print("FORMATTED FOR LLM:")
    print("=" * 80)
    print(formatted_thread)
    print("\n" + "=" * 80)

    # Load the prompt template
    prompt_file = "reddit_comment_insight_extraction_prompt.md"

    if not os.path.exists(prompt_file):
        print(f"\n❌ Error: {prompt_file} not found!")
        session.close()
        return

    with open(prompt_file, 'r') as f:
        prompt_template = f.read()

    # Combine prompt with thread
    full_prompt = prompt_template + "\n\n" + formatted_thread

    print("\n🤖 Making OpenAI API call...")
    print("=" * 80)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found!")
        print("\nPlease set it in .env file:")
        print("  OPENAI_API_KEY=your-api-key-here")
        print("\nOr set as environment variable:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        session.close()
        return

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Make API call
        response = client.chat.completions.create(
            model="gpt-5-mini",  # Using mini for cost efficiency
            messages=[
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            response_format={"type": "json_object"}  # Request JSON response
        )

        # Extract the response
        result_text = response.choices[0].message.content

        print("\n✅ API RESPONSE:")
        print("=" * 80)

        # Try to parse and pretty-print JSON
        try:
            result_json = json.loads(result_text)
            print(json.dumps(result_json, indent=2))

            # Show summary
            print("\n" + "=" * 80)
            print("📊 EXTRACTION SUMMARY:")
            print("=" * 80)
            print(f"Competitors mentioned: {len(result_json.get('competitors_mentioned', []))}")
            print(f"Sentiment score: {result_json.get('sentiment_score', 'null')}")
            print(f"Complaints extracted: {len(result_json.get('complaints', []))}")

        except json.JSONDecodeError:
            print(result_text)
            print("\n⚠️  Warning: Response is not valid JSON")

        print("\n" + "=" * 80)
        print(f"💰 Token usage: {response.usage.total_tokens} tokens")
        print(f"   Prompt: {response.usage.prompt_tokens}")
        print(f"   Completion: {response.usage.completion_tokens}")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error calling OpenAI API: {e}")

    session.close()


if __name__ == "__main__":
    test_prompt()
