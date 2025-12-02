# Reddit POST Use Case Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **use cases** about **Wispr Flow**, a voice-to-text dictation app, from Reddit posts. You will be given a single Reddit post (title + body) and need to classify how users are using Wispr Flow into predefined categories.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "use_cases": [
    {
      "category": "emails",
      "quote": "Exact quote from post"
    }
  ]
}
```

For the `other` category, include a description:

```json
{
  "category": "other",
  "other_description": "Writing fiction stories",
  "quote": "Exact quote from post"
}
```

### Field Definitions:

- **category**: One of the predefined categories: `emails`, `messaging`, `vibe_coding`, `prompting_llm`, `note_taking`, `brain_dump`, `on_the_go`, `accessibility`, `improving_english`, `content_creation`, `other`
- **other_description**: (Only for `other` category) Brief description of the use case
- **quote**: Direct quote from the post supporting this use case

### Rules:

- Only extract if clearly about Wispr Flow (use subreddit/context to determine)
- Each use case = one category. If someone uses it for multiple things, extract multiple use cases
- A single activity can map to multiple categories (e.g., "writing emails while walking" → `emails` + `on_the_go`)

---

## Few-Shot Examples

### Example 1: Multiple Categories

**POST:**

```
Title: Wispr Flow boosted my productivity 10x
Body: I've been using Wispr Flow for a few months now and it's been incredible. I mainly use it for:

1. Writing long emails to clients - way faster than typing
2. Taking meeting notes while on Zoom calls
3. Describing code changes to Cursor and Claude Code - vibe coding is amazing
4. Sending quick Slack messages while I'm cooking dinner

The AI formatting is spot on for emails. I can just ramble and it makes it sound professional.

Community: r/ProductivityApps
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "emails",
      "quote": "Writing long emails to clients - way faster than typing"
    },
    {
      "category": "note_taking",
      "quote": "Taking meeting notes while on Zoom calls"
    },
    {
      "category": "vibe_coding",
      "quote": "Describing code changes to Cursor and Claude Code - vibe coding is amazing"
    },
    {
      "category": "messaging",
      "quote": "Sending quick Slack messages while I'm cooking dinner"
    },
    {
      "category": "on_the_go",
      "quote": "Sending quick Slack messages while I'm cooking dinner"
    }
  ]
}
```

**Why this output?**
- Cursor/Claude Code → `vibe_coding` (code-focused AI tools)
- Slack while cooking → `messaging` + `on_the_go` (activity + context)
- Meeting notes → `note_taking`

---

### Example 2: Only CURRENT Use Cases (Skip Hypotheticals)

**POST:**

```
Title: Feature request: Better support for coding
Body: Would love to see better support for describing code to AI assistants like Cursor and Windsurf. Right now I use it for brain dumping ideas into Notion and writing emails, but I think it could be amazing for vibe coding.

Also, it would be great if it worked better while I'm driving.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "brain_dump",
      "quote": "brain dumping ideas into Notion"
    },
    {
      "category": "emails",
      "quote": "writing emails"
    }
  ]
}
```

**Why this output?**
- ✅ "brain dumping ideas" → `brain_dump` (current use)
- ✅ "writing emails" → `emails` (current use)
- ❌ "better support for coding" → SKIPPED (feature request)
- ❌ "it would be great while driving" → SKIPPED (hypothetical)

---

### Example 3: No Use Cases Found

**POST:**

```
Title: This app is a game changer!
Body: The dictation is so accurate and the smart formatting feature is incredible. Voice typing has never been this good!

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": []
}
```

**Why this is CORRECT:**
- Post only praises features/capabilities
- No mention of actual activities (emails, notes, coding, etc.)
- Empty array is valid when no real use cases found

---

### Example 4: Accessibility Use Case

**POST:**

```
Title: Life saver for my carpal tunnel
Body: I developed RSI from years of typing and Wispr Flow has been incredible. Now I can write all my work emails and Slack messages without any pain.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "accessibility",
      "quote": "I developed RSI from years of typing and Wispr Flow has been incredible"
    },
    {
      "category": "emails",
      "quote": "write all my work emails"
    },
    {
      "category": "messaging",
      "quote": "Slack messages without any pain"
    }
  ]
}
```

---

## Now Extract Use Cases from This Post:

[POST WILL BE PROVIDED HERE]
