#!/usr/bin/env python3
"""
Script to remove prompt_version references from all scripts except extract_insights.py
"""

import re
from pathlib import Path

# Files to update
FILES_TO_UPDATE = [
    "label_clusters.py",
    "generate_dashboard_data.py",
    "semantic_grouping.py",
    "generate_reduced_embeddings.py",
    "hierarchical_clustering.py",
    "review_insights_report.py"
]

def remove_prompt_version_from_file(filepath: Path) -> tuple[str, int]:
    """Remove all prompt_version references from a file"""

    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content
    changes_made = 0

    # 1. Remove prompt_version parameter from function signatures (with Optional and default)
    # Pattern: prompt_version: Optional[int] = None,
    # Pattern: prompt_version: int = 2,
    # Pattern: prompt_version: int,
    content, n = re.subn(
        r',?\s*prompt_version:\s*(Optional\[)?int(\])?\s*(=\s*\d+)?\s*,',
        ',',
        content
    )
    changes_made += n

    # Clean up double commas that might have been created
    content = re.sub(r',\s*,', ',', content)

    # 2. Remove from Args documentation
    content, n = re.subn(
        r'\s+prompt_version:.*?\n',
        '',
        content
    )
    changes_made += n

    # 3. Remove argparse --prompt-version argument
    content, n = re.subn(
        r'    parser\.add_argument\(\s*["\']--prompt-version["\'].*?\)\n',
        '',
        content,
        flags=re.DOTALL
    )
    changes_made += n

    # 4. Remove from WHERE clauses
    # Pattern: AND prompt_version = :version
    content, n = re.subn(
        r'\s+AND prompt_version = :version',
        '',
        content
    )
    changes_made += n

    # Pattern: WHERE Cluster.prompt_version == prompt_version
    content, n = re.subn(
        r',?\s*Cluster\.prompt_version\s*==\s*prompt_version\s*,?',
        '',
        content
    )
    changes_made += n

    # 5. Remove from params dictionaries
    # Pattern: "version": prompt_version,
    content, n = re.subn(
        r',?\s*["\']version["\']\s*:\s*prompt_version\s*,?',
        '',
        content
    )
    changes_made += n

    # Clean up empty params or trailing commas in dicts
    content = re.sub(r'\{\s*,', '{', content)
    content = re.sub(r',\s*\}', '}', content)

    # 6. Remove from print statements mentioning prompt version
    content, n = re.subn(
        r'\s+print\(f?["\'].*?[Pp]rompt version.*?\n',
        '',
        content
    )
    changes_made += n

    # 7. Remove from output filenames
    # Pattern: _v{prompt_version}
    content, n = re.subn(
        r'_v\{prompt_version\}',
        '',
        content
    )
    changes_made += n

    # 8. Remove prompt_version from function calls
    # Pattern: prompt_version=args.prompt_version,
    # Pattern: prompt_version=prompt_version,
    content, n = re.subn(
        r',?\s*prompt_version\s*=\s*[a-zA-Z_\.]+\s*,?',
        '',
        content
    )
    changes_made += n

    # Clean up multiple consecutive blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)

    # Clean up trailing commas before closing parenthesis
    content = re.sub(r',\s*\)', ')', content)

    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)

    return filepath.name, changes_made


def main():
    base_dir = Path(__file__).parent

    print("=" * 60)
    print("REMOVING PROMPT_VERSION REFERENCES")
    print("=" * 60)

    total_changes = 0

    for filename in FILES_TO_UPDATE:
        filepath = base_dir / filename
        if not filepath.exists():
            print(f"⚠️  {filename}: NOT FOUND")
            continue

        name, changes = remove_prompt_version_from_file(filepath)
        total_changes += changes
        print(f"✅ {name}: {changes} changes")

    print("=" * 60)
    print(f"TOTAL CHANGES: {total_changes}")
    print("=" * 60)


if __name__ == "__main__":
    main()
