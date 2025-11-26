#!/usr/bin/env python3
"""
Test the post insight extraction prompt with a sample post and make an OpenAI API call
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from models import RedditContent, get_session

# Load environment variables from .env file
load_dotenv()


def format_post_for_prompt(post: RedditContent) -> str:
    """Format a post in the format expected by the prompt"""
    output = "**POST:**\n\n```\n"

    if post.title:
        output += f"Title: {post.title}\n"
    if post.body:
        output += f"Body: {post.body}\n"

    output += f"\nCommunity: {post.community_name}\n"
    output += "```"

    return output


def test_post_prompt():
    """Test the prompt with a sample post and call OpenAI API"""
    session = get_session()

    # Get a post with good content
    # Let's use the "Wispr Flow is a scam" post - lots of complaints
    post = session.query(RedditContent).filter(
        RedditContent.content_type == 'post',
        RedditContent.title.like('%scam%')
    ).first()

    if not post:
        # Fallback to any post with body
        post = session.query(RedditContent).filter(
            RedditContent.content_type == 'post',
            RedditContent.body.isnot(None)
        ).first()

    if not post:
        print("No suitable post found!")
        return

    print("=" * 80)
    print("TEST POST INSIGHT EXTRACTION PROMPT")
    print("=" * 80)
    print(f"\nPost ID: {post.id}")
    print(f"Title: {post.title}\n")

    # Format the post
    formatted_post = format_post_for_prompt(post)

    print("FORMATTED FOR LLM:")
    print("=" * 80)
    print(formatted_post)
    print("\n" + "=" * 80)

    # Load the prompt template
    prompt_file = "reddit_post_insight_extraction_prompt.md"

    if not os.path.exists(prompt_file):
        print(f"\n❌ Error: {prompt_file} not found!")
        session.close()
        return

    with open(prompt_file, 'r') as f:
        prompt_template = f.read()

    # Combine prompt with post
    full_prompt = prompt_template + "\n\n" + formatted_post

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
    test_post_prompt()
