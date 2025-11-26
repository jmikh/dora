"""
Prompt Builder Utility

Loads and combines shared prompt components with specific prompt templates
"""

from pathlib import Path
from typing import Dict


def load_file(filename: str) -> str:
    """Load a file from the project directory"""
    file_path = Path(__file__).parent / filename
    with open(file_path, 'r') as f:
        return f.read()


def build_prompt(prompt_type: str) -> str:
    """
    Build a complete prompt by combining shared components with specific template

    Args:
        prompt_type: One of 'reddit_comment', 'reddit_post', 'review'

    Returns:
        Complete prompt string ready to use
    """
    # Load shared components
    shared_components = load_file("prompt_shared_components.md")

    # Extract sections from shared components
    components = parse_shared_components(shared_components)

    # Load specific template
    if prompt_type == 'reddit_comment':
        template = load_file("reddit_comment_insight_extraction_prompt.md")
    elif prompt_type == 'reddit_post':
        template = load_file("reddit_post_insight_extraction_prompt.md")
    elif prompt_type == 'review':
        template = load_file("review_insight_extraction_prompt.md")
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

    # Replace placeholders in template with shared components
    prompt = template.replace("{{WISPR_FLOW_DESCRIPTION}}", components['wispr_flow'])
    prompt = prompt.replace("{{OUTPUT_SCHEMA}}", components['output_schema'])
    prompt = prompt.replace("{{FIELD_DEFINITIONS}}", components['field_definitions'])

    return prompt


def parse_shared_components(content: str) -> Dict[str, str]:
    """Parse shared components file into sections"""
    sections = {}

    lines = content.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        if line.startswith('## What is Wispr Flow?'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'wispr_flow'
            current_content = []
        elif line.startswith('## Output Schema'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'output_schema'
            current_content = []
        elif line.startswith('## Field Definitions'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'field_definitions'
            current_content = []
        elif line.startswith('## Core Extraction Rules'):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = 'core_rules'
            current_content = []
        elif not line.startswith('# ') and not line.startswith('---'):
            current_content.append(line)

    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()

    return sections


# For backward compatibility - direct load functions
def load_reddit_comment_prompt() -> str:
    """Load complete Reddit comment extraction prompt"""
    return build_prompt('reddit_comment')


def load_reddit_post_prompt() -> str:
    """Load complete Reddit post extraction prompt"""
    return build_prompt('reddit_post')


def load_review_prompt() -> str:
    """Load complete review extraction prompt"""
    return build_prompt('review')
