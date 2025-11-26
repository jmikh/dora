# Prompt Maintenance Guide

This document describes the shared components across all three extraction prompts and how to maintain consistency when making updates.

## Prompt Files

1. **`reddit_comment_insight_extraction_prompt.md`** - For Reddit comments with thread context
2. **`reddit_post_insight_extraction_prompt.md`** - For Reddit posts (no thread context)
3. **`review_insight_extraction_prompt.md`** - For app store reviews

## Shared Components

The following sections are **shared across all three prompts** and should be kept in sync when making changes:

### 1. What is Wispr Flow? ✅ IDENTICAL

**Location:** Near top of each prompt

**Content:**
```markdown
Wispr Flow is a voice dictation app that users commonly use for:
- **Writing emails** (Gmail, Outlook, Superhuman)
- **Messaging** (Slack, Discord, iMessage, WhatsApp, Teams)
- **AI prompting** (ChatGPT, Claude, Cursor, Windsurf)
- **Coding assistance** ("vibe coding" - describing code to AI assistants)
- **Note-taking** (Notion, Obsidian, Apple Notes, brain dumping ideas)
- **Documentation** (writing docs, creating content)
```

**When to update:** When Wispr Flow adds new major use cases or integrations

---

### 2. Output Schema ✅ IDENTICAL

**Location:** After critical rules in each prompt

**Content:**
```json
{
  "competitors_mentioned": ["Competitor1", "Competitor2"],
  "sentiment_score": 4,
  "complaints": [
    {
      "complaint": "Brief description of complaint",
      "quote": "Exact quote from content"
    }
  ]
}
```

**When to update:** If we add new fields to the extraction (e.g., `feature_requests`, `use_cases`)

---

### 3. Competitor Examples ✅ IDENTICAL

**Field:** `competitors_mentioned`

**Examples:**
- Spokenly
- Vowen
- FluidVoice
- VoiceInk
- Superwhisper
- Talon
- Dragon NaturallySpeaking
- Siri
- Willow Voice
- Microsoft Dictation
- Noteflux

**When to update:** When new competitors emerge or are frequently mentioned

---

### 4. Sentiment Score Scale ⚠️ SIMILAR (minor differences)

**Shared scale:**
- **1** = Very negative (angry, frustrated, demanding refund, calling it unusable)
- **2** = Somewhat negative (disappointed, multiple complaints, wouldn't recommend)
- **3** = Neutral (has opinion but mixed/balanced)
- **4** = Somewhat positive (happy, works well, minor complaints)
- **5** = Very positive (love it, game-changer, highly recommend, enthusiastic)
- **null** = No sentiment expressed OR purely factual/informational content

**Differences:**
- **Reddit prompts**: More emphasis on "support responses, how-to answers, neutral questions" → null
- **Review prompt**: Explicitly states "Do NOT look at the star rating"

**When to update:** If we refine what constitutes each sentiment level

---

### 5. Complaint Extraction Rules ✅ HIGHLY SIMILAR

**Shared rules:**

#### Be Specific
- ❌ BAD: "Setting doesn't work"
- ✅ GOOD: "Smart Formatting doesn't work"
- ❌ BAD: "Poor device support"
- ✅ GOOD: "Poor Bluetooth microphone support"

#### Aggressive Deduplication
Combine complaints about the same CORE ISSUE:
- "Forced AI formatting" + "Can't disable AI formatting" → "Cannot disable AI formatting"
- "App crashes" + "App freezes" + "App disconnects" → "Frequent crashes and freezes"
- "Bluetooth doesn't work" + "AirPods not recognized" → "Poor Bluetooth microphone support"
- "Slow transcription" + "Takes too long to process" → "Slow transcription speed"

#### Formatting Requirements
- Keep complaint text SHORT (5-10 words max)
- Use simple, jargon-free language
- Remove app name (don't say "Wispr Flow")
- Normalize for clustering
- Make clear enough to understand standalone
- Include specific feature/setting names

**Differences:**
- **Reddit comment prompt**: Additional rule about using thread context to enrich pronouns ("it" → "Smart Formatting")
- **Reddit post prompt**: Slightly less context enrichment (no thread)
- **Review prompt**: No thread context (simpler)

**When to update:** When we identify new patterns of complaints that should be deduplicated

---

### 6. Core Extraction Rules ✅ SHARED PRINCIPLES

**Common across all:**
1. Only extract insights specifically about Wispr Flow
2. If competitor app has issues, do NOT extract as Wispr Flow complaints
3. If sentiment not about Wispr Flow, return `null`
4. Factual/informational = `null` sentiment

**Prompt-specific:**
- **Reddit comment**: "Extract ONLY from TARGET comment (not context)"
- **Reddit post**: Applies to entire post
- **Review**: "Do NOT use star rating to infer sentiment"

---

## Maintenance Workflow

### When Making Updates

1. **Identify which component you're changing** (use list above)

2. **Determine scope:**
   - **Shared component**: Update in ALL three prompts
   - **Prompt-specific**: Update only the relevant prompt

3. **Update order** (to maintain consistency):
   - Start with Reddit comment prompt (most comprehensive)
   - Copy shared changes to Reddit post prompt
   - Copy shared changes to review prompt
   - Adjust prompt-specific details

4. **Test changes:**
   ```bash
   # Test each processor with --limit 1 --verbose
   python reddit_content_processor.py --limit 1 -v
   python review_processor.py --limit 1 -v
   ```

5. **Document changes** in this file if adding new shared components

---

## Quick Reference: What's Different?

### Reddit Comment Prompt (Most Complex)
- Has thread context rules
- "Use Thread Context to Enrich Complaints" section
- Most examples (7 examples)
- Focuses on TARGET comment vs context distinction

### Reddit Post Prompt (Medium)
- No thread context
- Slightly simpler complaint enrichment rules
- 6 examples
- Uses subreddit/post content for context

### Review Prompt (Simplest)
- No thread context
- Explicitly excludes star rating from LLM
- 10 examples (most examples but simplest structure)
- Focuses on text-only sentiment inference

---

## Common Update Scenarios

### Adding a New Competitor
**Files to update:** All three prompts
**Location:** `competitors_mentioned` examples section
**Example:** Add "NewApp" to the examples list

### Adding a New Use Case
**Files to update:** All three prompts
**Location:** "What is Wispr Flow?" section
**Example:** Add "- **Meeting transcription** (Zoom, Google Meet)"

### Refining Deduplication Rules
**Files to update:** All three prompts
**Location:** "CRITICAL - Aggressive Deduplication" section
**Example:** Add new pattern like "Poor Windows support" + "Doesn't work on PC" → "Poor Windows/PC support"

### Changing Sentiment Scale
**Files to update:** All three prompts (with prompt-specific notes)
**Location:** `sentiment_score` definition
**Example:** Change level 3 from "Neutral" to "Mixed"

### Adding New Field to Schema
**Files to update:** All three prompts + processors + models.py
**Example:** Add `use_cases_mentioned` field

---

## Validation Checklist

Before committing prompt changes, verify:

- [ ] Shared components are identical across all prompts
- [ ] JSON schema is identical across all prompts
- [ ] Competitor examples list is identical
- [ ] Sentiment scale levels are consistent
- [ ] Deduplication examples are identical
- [ ] Formatting requirements are identical
- [ ] Tested with --limit 1 --verbose on each processor
- [ ] No regressions in extraction quality

---

## Future Improvements

Consider these optimizations:

1. **Template system**: Extract truly shared components into separate file
2. **Automated testing**: Unit tests for each prompt with expected outputs
3. **Version tracking**: Track prompt versions and performance metrics
4. **A/B testing**: Test prompt variations on subset of data
