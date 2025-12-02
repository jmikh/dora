# Reddit COMMENT Use Case Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **use cases** about **Wispr Flow**, a voice-to-text dictation app, from Reddit comments. You will be given a comment with its full thread context and need to classify how users are using Wispr Flow into predefined categories.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "use_cases": [
    {
      "category": "emails",
      "quote": "Exact quote from comment"
    }
  ]
}
```

For the `other` category, include a description:

```json
{
  "category": "other",
  "other_description": "Writing fiction stories",
  "quote": "Exact quote from comment"
}
```

### Field Definitions:

- **category**: One of the predefined categories: `emails`, `messaging`, `vibe_coding`, `prompting_llm`, `note_taking`, `brain_dump`, `on_the_go`, `accessibility`, `improving_english`, `content_creation`, `other`
- **other_description**: (Only for `other` category) Brief description of the use case
- **quote**: Direct quote from the TARGET COMMENT (not context)

### Rules:

- Only extract if clearly about Wispr Flow (use thread context to determine)
- Each use case = one category. If someone uses it for multiple things, extract multiple use cases
- A single activity can map to multiple categories

---

## Few-Shot Examples

### Example 1: Multiple Categories

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: What do you use Wispr Flow for?
Body: Curious what everyone's main use cases are

Community: r/WisprFlow
```

**TARGET COMMENT:**

```
I use it constantly for work. Mainly for writing emails to my team, taking notes during 1-on-1s, and describing features to Cursor when I'm building stuff. Game changer for productivity.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "emails",
      "quote": "writing emails to my team"
    },
    {
      "category": "note_taking",
      "quote": "taking notes during 1-on-1s"
    },
    {
      "category": "vibe_coding",
      "quote": "describing features to Cursor when I'm building stuff"
    }
  ]
}
```

**Why this output?**
- Cursor → `vibe_coding` (code-focused AI tool)
- Meeting notes → `note_taking`

---

### Example 2: Only CURRENT Use Cases (Skip Hypotheticals)

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Feature requests for Wispr Flow
Body: What features would you like to see?

Community: r/WisprFlow
```

**TARGET COMMENT:**

```
Would love better support for coding in Cursor. Right now I mainly use it for emails but could see it being useful for describing code to AI.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "emails",
      "quote": "Right now I mainly use it for emails"
    }
  ]
}
```

**Why this output?**
- ✅ `emails` (current use)
- ❌ "better support for coding" → SKIPPED (feature request)
- ❌ "could see it being useful" → SKIPPED (hypothetical)

---

### Example 3: No Use Cases Found

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: This app is amazing
Body: Just wanted to share my experience

Community: r/WisprFlow
```

**TARGET COMMENT:**

```
The dictation is incredible. Smart formatting works great!
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": []
}
```

**Why:** Only praises features, no specific category of use mentioned.

---

## Now Extract Use Cases from This Comment:

[THREAD CONTEXT AND TARGET COMMENT WILL BE PROVIDED HERE]
