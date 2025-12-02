"""
Merge duplicate competitor names in the database.
Creates a competitors table with canonical names and tracks alternative naming.
Updates competitor_mentions to use canonical names.
"""

import sqlite3
from datetime import datetime

DB_PATH = "dora.db"

# Define merge mappings: canonical_name -> list of alternatives
MERGE_MAPPINGS = {
    "SuperWhisper": [
        "Super Whisper",
        "Super whisper",
        "Superwhisper",
        "superwhisper",
    ],
    "Aqua Voice": [
        "Aqua",
        "Aquavoice",
    ],
    "VoiceInk": [
        "Voice Ink",
    ],
    "Siri": [
        "SIRI",
        "Hey Siri",
    ],
    "Claude": [
        "Claude Code",
        "Claude Codes",
    ],
    "Willow Voice": [
        "Willow",
        "Willow AI",
        "Willow Voice AI",
    ],
    "Wispr Flow": [
        "WisprFlow",
        "Apple Wispr app",
        "Wispr Type",
    ],
    "saytotype.ai": [
        "syatotype",
    ],
    "Apple Dictation": [
        "Apple",
        "Apple dictation",
        "Apple voice-to-text",
        "Apple's Voice-to-Text",
        "Apple's native speech-to-text",
        "Apple's built-in voice dictation",
        "Apple built-in voice to text",
        "Apple transcription",
        "built-in dictation",
        "Dictation",
        "iOS built-in app",
        "iOS native app",
        "iPhone dictation",
        "iPhone transcription",
    ],
    "Windows Dictation": [
        "Windows built-in speech to text",
        "inbuilt speech tool in windows",
        "Microsoft Dictation",
    ],
}


def merge_competitors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create competitors table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            alternative_names TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Get all distinct competitor names currently in mentions
    cursor.execute("SELECT DISTINCT competitor_name FROM competitor_mentions")
    all_names = {row[0] for row in cursor.fetchall()}

    # Build reverse mapping: alternative -> canonical
    alt_to_canonical = {}
    for canonical, alternatives in MERGE_MAPPINGS.items():
        for alt in alternatives:
            alt_to_canonical[alt] = canonical

    # Track what we're merging
    merge_stats = {}

    # Update competitor_mentions with canonical names
    for alt_name, canonical_name in alt_to_canonical.items():
        if alt_name in all_names:
            cursor.execute(
                "UPDATE competitor_mentions SET competitor_name = ? WHERE competitor_name = ?",
                (canonical_name, alt_name)
            )
            updated = cursor.rowcount
            if updated > 0:
                if canonical_name not in merge_stats:
                    merge_stats[canonical_name] = []
                merge_stats[canonical_name].append((alt_name, updated))
                print(f"  Merged '{alt_name}' -> '{canonical_name}' ({updated} rows)")

    # Now get all unique competitor names after merging
    cursor.execute("SELECT DISTINCT competitor_name FROM competitor_mentions")
    final_names = {row[0] for row in cursor.fetchall()}

    # Insert into competitors table
    for name in final_names:
        # Get alternative names if this was a merge target
        alternatives = MERGE_MAPPINGS.get(name, [])
        # Only include alternatives that actually existed in the data
        actual_alternatives = [alt for alt in alternatives if alt in all_names]
        alt_string = ", ".join(actual_alternatives) if actual_alternatives else None

        cursor.execute("""
            INSERT OR REPLACE INTO competitors (name, alternative_names)
            VALUES (?, ?)
        """, (name, alt_string))

    conn.commit()

    # Print summary
    print("\n" + "="*60)
    print("MERGE SUMMARY")
    print("="*60)

    for canonical, merged_items in merge_stats.items():
        total_rows = sum(count for _, count in merged_items)
        alt_names = [name for name, _ in merged_items]
        print(f"\n{canonical}:")
        print(f"  Merged from: {', '.join(alt_names)}")
        print(f"  Total rows updated: {total_rows}")

    # Show final competitor count
    cursor.execute("SELECT COUNT(*) FROM competitors")
    count = cursor.fetchone()[0]
    print(f"\n{'='*60}")
    print(f"Total unique competitors after merge: {count}")
    print(f"Original unique names: {len(all_names)}")
    print(f"Names merged: {len(all_names) - len(final_names)}")

    conn.close()


if __name__ == "__main__":
    merge_competitors()
