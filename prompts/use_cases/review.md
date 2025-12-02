# Review Use Case Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **use cases** about **Wispr Flow**, a voice-to-text dictation app, from app store reviews. You will be given a single review (rating + text) and need to classify how users are using Wispr Flow into predefined categories.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "use_cases": [
    {
      "category": "emails",
      "quote": "Exact quote from review"
    }
  ]
}
```

For the `other` category, include a description:

```json
{
  "category": "other",
  "other_description": "Writing fiction stories",
  "quote": "Exact quote from review"
}
```

### Field Definitions:

- **category**: One of the predefined categories: `emails`, `messaging`, `vibe_coding`, `prompting_llm`, `note_taking`, `brain_dump`, `on_the_go`, `accessibility`, `improving_english`, `content_creation`, `other`
- **other_description**: (Only for `other` category) Brief description of the use case
- **quote**: Direct quote from the review supporting this use case

### Rules:

- Each use case = one category. If someone uses it for multiple things, extract multiple use cases
- A single activity can map to multiple categories (e.g., "writing emails while walking" → `emails` + `on_the_go`)

---

## Few-Shot Examples

### Example 1: Multiple Categories

**REVIEW:**

```
Rating: 5 stars
Review: As of now, I am using Wispr Flow. It is very good as I use it to write notes, write essays with just my voice, and write emails. And also write messages. I really recommend this app as it's really made my life easier.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "note_taking",
      "quote": "write notes"
    },
    {
      "category": "content_creation",
      "quote": "write essays with just my voice"
    },
    {
      "category": "emails",
      "quote": "write emails"
    },
    {
      "category": "messaging",
      "quote": "write messages"
    }
  ]
}
```

---

### Example 2: On-the-Go + Messaging

**REVIEW:**

```
Rating: 5 stars
Review: I'm always on the go and working from my phone. So it's fantastic to finally have an option to talk and walk and get work done without having to worry about constantly looking at the screen to format my messaging.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "on_the_go",
      "quote": "talk and walk and get work done"
    },
    {
      "category": "messaging",
      "quote": "format my messaging"
    }
  ]
}
```

---

### Example 3: No Use Cases Found

**REVIEW:**

```
Rating: 4 stars
Review: Great app for dictating. The smart formatting feature is amazing.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": []
}
```

**Why:** Only praises features, no specific category of use mentioned.

---

### Example 4: "Other" Category

**REVIEW:**

```
Rating: 5 stars
Review: I use Wispr Flow to write my fantasy novels. It's so much faster than typing and I can get my creative ideas out while they're fresh.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "other",
      "other_description": "Writing fiction/novels",
      "quote": "use Wispr Flow to write my fantasy novels"
    }
  ]
}
```

---

### Example 5: ESL User

**REVIEW:**

```
Rating: 5 stars
Review: English is my second language and Wispr Flow helps me write better emails. The AI fixes my grammar mistakes automatically!
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "category": "improving_english",
      "quote": "English is my second language and Wispr Flow helps me write better"
    },
    {
      "category": "emails",
      "quote": "write better emails"
    }
  ]
}
```

---

## Now Extract Use Cases from This Review:

[REVIEW WILL BE PROVIDED HERE]
