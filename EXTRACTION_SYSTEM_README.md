# Extraction System Documentation

## Overview

This system extracts **complaints** and **use cases** from Reddit posts/comments and app store reviews using OpenAI LLM.

## Directory Structure

```
dora/
├── prompts/
│   ├── complaints/
│   │   ├── common.md              # Shared rules for complaint extraction
│   │   ├── reddit_post.md         # Reddit post complaint prompt
│   │   ├── reddit_comment.md      # Reddit comment complaint prompt
│   │   └── review.md              # Review complaint prompt
│   └── use_cases/
│       ├── common.md              # Shared rules for use case extraction
│       ├── reddit_post.md         # Reddit post use case prompt
│       ├── reddit_comment.md      # Reddit comment use case prompt
│       └── review.md              # Review use case prompt
├── extraction_core.py             # Shared extraction logic
├── extract_content.py             # Unified CLI (NEW!)
├── reddit_content_processor.py    # Reddit-specific processor
├── review_processor.py            # Review-specific processor
└── models.py                      # SQLAlchemy models (includes UseCase)
```

## Database Tables

### `complaints`
- Stores extracted complaints with quote and source reference
- Fields: `id`, `complaint`, `quote`, `source_id`, `source_table`, `extracted_at`

### `use_cases` (NEW!)
- Stores extracted use cases with quote and source reference
- Fields: `id`, `use_case`, `quote`, `source_id`, `source_table`, `extracted_at`
- **Important**: Use cases are atomic and singular (e.g., "Writing emails", not "Sending emails while driving")

## Usage

### Unified CLI (Recommended)

Extract complaints and/or use cases using the unified interface:

```bash
# Extract complaints only
python extract_content.py --company wispr --type complaints --limit 10

# Extract use cases only
python extract_content.py --company wispr --type use_cases --limit 10

# Extract both
python extract_content.py --company wispr --type both --limit 10

# Specific source
python extract_content.py --company wispr --type use_cases --source reddit --limit 5
python extract_content.py --company wispr --type complaints --source reviews --limit 5
```

### Legacy Scripts (Still Work)

```bash
# Reddit complaints (legacy)
python reddit_content_processor.py --limit 10 --verbose

# Review complaints (legacy)
python review_processor.py --limit 10 --verbose
```

## Prompt System

### Common Rules

Both `prompts/complaints/common.md` and `prompts/use_cases/common.md` contain:
- Wispr Flow product description
- Extraction rules (specificity, deduplication, formatting)
- Competitor examples
- Sentiment scoring guidelines

Prompts reference common rules via `{{COMMON_RULES}}` placeholder, which is automatically replaced at runtime.

### Complaint Extraction Rules

- **Be Specific**: Include feature names ("Smart Formatting doesn't work" not "Setting doesn't work")
- **Aggressive Deduplication**: Combine similar issues into ONE complaint
- **Short Format**: 5-10 words max
- **Normalized**: Ready for clustering

### Use Case Extraction Rules (NEW!)

- **Atomic**: Break compound use cases into singular actions
  - ❌ "Sending emails while driving" → ✅ ["Writing emails", "Dictating while driving"]
- **Gerund Form**: Use verb+-ing ("Writing emails", "Taking notes")
- **Deduplication**: Combine semantically similar use cases
- **Short Format**: 2-5 words max

## Core Functions

### `extraction_core.py`

- `load_prompt(path)` - Load prompt with common rules replacement
- `call_llm(prompt, client, model)` - Call OpenAI API
- `save_complaints(source_id, source_table, complaints)` - Save complaints to DB
- `save_use_cases(source_id, source_table, use_cases)` - Save use cases to DB
- `save_sentiment(source_id, source_table, sentiment_score)` - Save sentiment
- `save_competitor_mentions(source_id, source_table, competitors)` - Save competitors

## Examples

### Example: Extract Use Cases from Reddit

```bash
python extract_content.py --company wispr --type use_cases --source reddit --limit 5
```

**Output:**
```
================================================================================
EXTRACTING USE_CASES FROM REDDIT
================================================================================
✓ Loaded prompts from prompts/use_cases/
✓ OpenAI client initialized
✓ Found 150 unprocessed records (processing: 5)

[1/5] Processing post t3_abc123...
  ✓ Saved 3 use cases
[2/5] Processing comment t1_def456...
  ✓ Saved 2 use cases
...
```

### Example: Extract Both Complaints and Use Cases

```bash
python extract_content.py --company wispr --type both --limit 10
```

This will:
1. Extract complaints from each piece of content
2. Extract use cases from the same content
3. Save sentiment and competitor mentions
4. Mark content as processed

## Use Case Breakdown Example

**Input:** "I use Wispr Flow for sending emails while driving"

**Extracted Use Cases:**
1. `{"use_case": "Writing emails", "quote": "sending emails while driving"}`
2. `{"use_case": "Dictating while driving", "quote": "sending emails while driving"}`

**Why?** The system breaks compound use cases into atomic actions for better analysis.

## Migration from Old System

### Old Way (Still Works)
```python
from example_ai_extraction import save_extraction_results

save_extraction_results(
    source_id="t3_abc",
    source_table="reddit_content",
    ai_response={
        "complaints": [...],
        "sentiment_score": 4,
        "competitors_mentioned": [...]
    }
)
```

### New Way (Recommended)
```python
from extraction_core import save_complaints, save_sentiment, save_competitor_mentions

save_sentiment(source_id, source_table, sentiment_score, mark_processed=True)
save_competitor_mentions(source_id, source_table, competitors)
save_complaints(source_id, source_table, complaints)
save_use_cases(source_id, source_table, use_cases)  # NEW!
```

## Tips

1. **Start Small**: Use `--limit 10` to test extraction before processing all content
2. **Use Verbose**: Add `-v` flag to see LLM responses and debug issues
3. **Check Prompts**: Review `prompts/*/common.md` to understand extraction rules
4. **Atomic Use Cases**: Remember use cases should be singular actions, not compound scenarios

## Troubleshooting

### "No prompts found"
- Check that `prompts/` directory exists with `complaints/` and `use_cases/` subdirectories
- Ensure `common.md` files exist in both subdirectories

### "OPENAI_API_KEY not found"
- Set environment variable: `export OPENAI_API_KEY=sk-...`
- Or add to `.env` file: `OPENAI_API_KEY=sk-...`

### "No unprocessed records"
- All content is already processed
- To reprocess, set `ai_processed=False` in database
- Or add new content via scrapers

## Next Steps

After extracting use cases:
1. **View Use Cases**: Query `use_cases` table to see what users are doing
2. **Cluster Use Cases**: Similar to complaint clustering, group similar use cases
3. **Analyze Trends**: Identify most common use cases and their sources
4. **Feature Planning**: Use use case insights for product roadmap

## Files Modified

✅ **New Files:**
- `prompts/complaints/common.md`
- `prompts/use_cases/common.md`
- `prompts/use_cases/reddit_post.md`
- `prompts/use_cases/reddit_comment.md`
- `prompts/use_cases/review.md`
- `extraction_core.py`
- `extract_content.py`
- `create_use_cases_table.py`

✅ **Updated Files:**
- `models.py` - Added `UseCase` model
- `reddit_content_processor.py` - Uses `extraction_core` functions and new prompt paths
- `review_processor.py` - Uses `extraction_core` functions and new prompt paths
- `example_ai_extraction.py` - Added use case support (deprecated, use `extraction_core` instead)

✅ **Moved Files:**
- `reddit_post_insight_extraction_prompt.md` → `prompts/complaints/reddit_post.md`
- `reddit_comment_insight_extraction_prompt.md` → `prompts/complaints/reddit_comment.md`
- `review_insight_extraction_prompt.md` → `prompts/complaints/review.md`
