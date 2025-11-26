# Review Use Case Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **use cases** about **Wispr Flow**, a voice-to-text dictation app, from app store reviews. You will be given a single review (rating + text) and need to extract how users are using or want to use Wispr Flow.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "use_cases": [
    {
      "use_case": "Writing emails",
      "quote": "Exact quote from review"
    }
  ]
}
```

### Field Definitions:

- **use_cases**: List of specific ways users are using or want to use **Wispr Flow**
  - Each use case must have a direct quote from the review
  - Include both explicit use cases ("I use it for X") and implicit ones ("Great for Y")
  - **CRITICAL**: Break compound use cases into ATOMIC, SINGULAR actions
  - **IMPORTANT - Formatting**:
    - Keep use case text SHORT (2-5 words max)
    - Use gerund form (verb + -ing)
    - Focus on the ACTION

---

## Few-Shot Examples (Using Real Reviews)

### Example 1: Multiple Distinct Use Cases (Real Review)

**REVIEW:**

```
Rating: 5 stars
Review: As of now, I am using Wispr Flow. It is very good as I use it to write notes, write essays with just my voice, and write emails. And also write messages. I really recommend this app as it's really made my life easier and just easy. Really in general with writing. I recommend giving this a try. If you haven't, do it.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "use_case": "Writing notes",
      "quote": "write notes"
    },
    {
      "use_case": "Writing essays",
      "quote": "write essays with just my voice"
    },
    {
      "use_case": "Writing emails",
      "quote": "write emails"
    },
    {
      "use_case": "Sending messages",
      "quote": "write messages"
    }
  ]
}
```

**Why this output?**
- **CRITICAL**: Each use case extracted separately, NOT combined
- Each represents a distinct activity/persona: note-taker, essay writer, emailer, messenger
- NO generic "Dictating" - each specifies WHAT they're writing

---

### Example 2: Context-Based Use Cases (Real Review)

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
      "use_case": "Working on mobile",
      "quote": "working from my phone"
    },
    {
      "use_case": "Working while walking",
      "quote": "talk and walk and get work done"
    },
    {
      "use_case": "Sending messages",
      "quote": "format my messaging"
    }
  ]
}
```

**Why this output?**
- Context-based use cases: "on mobile" and "while walking" are WHEN/WHERE they work
- Each use case is separated (not "working on mobile while walking")
- "Messaging" specifies WHAT they're doing
- NO generic "hands-free" or "dictating" - specific context provided

---

### Example 3: ❌ BAD vs ✅ GOOD - Feature vs Use Case

**REVIEW:**

```
Rating: 4 stars
Review: Great app for dictating. The smart formatting feature is amazing.
```

**❌ WRONG OUTPUT (DO NOT DO THIS):**

```json
{
  "use_cases": [
    {
      "use_case": "Dictating",
      "quote": "Great app for dictating"
    },
    {
      "use_case": "Smart formatting",
      "quote": "The smart formatting feature"
    }
  ]
}
```

**Why this is WRONG:**
- "Dictating" is too generic - that's just what Wispr does, not a use case
- "Smart formatting" is a FEATURE, not a use case

**✅ CORRECT OUTPUT:**

```json
{
  "use_cases": []
}
```

**Why this is CORRECT:**
- Review doesn't mention WHAT they're dictating or WHEN/WHERE
- No actual use case extracted, just praise for features
- It's OK to return empty use_cases if none found

---

### Example 4: ❌ BAD - Generic "Writing" is NOT a use case

**REVIEW:**

```
Rating: 5 stars
Review: I'm writing this review with Wispr Flow. It's helped me with all my projects and made things easier.
```

**❌ WRONG OUTPUT (DO NOT DO THIS):**

```json
{
  "use_cases": [
    {
      "use_case": "Writing",
      "quote": "I'm writing this"
    },
    {
      "use_case": "Writing reviews",
      "quote": "writing this review with Wispr Flow"
    },
    {
      "use_case": "Working on projects",
      "quote": "helped me with all my projects"
    }
  ]
}
```

**Why this is WRONG:**
- "Writing" is too generic - that's what the app does! WHAT are they writing?
- "Writing reviews" is meta - they're just reviewing the app, not a real use case
- "Working on projects" is too vague - what KIND of projects?

**✅ CORRECT OUTPUT:**

```json
{
  "use_cases": []
}
```

**Why this is CORRECT:**
- No specific use cases mentioned (no emails, notes, code, messages, etc.)
- No specific contexts mentioned (no driving, meetings, walking, etc.)
- Generic praise doesn't reveal HOW they actually use Wispr

---

## Now Extract Use Cases from This Review:

[REVIEW WILL BE PROVIDED HERE]
