# Reddit COMMENT Use Case Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **use cases** about **Wispr Flow**, a voice-to-text dictation app, from Reddit comments. You will be given a comment with its full thread context and need to extract how users are using or want to use Wispr Flow.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "use_cases": [
    {
      "use_case": "Writing emails",
      "quote": "Exact quote from comment"
    }
  ]
}
```

### Field Definitions:

- **use_cases**: List of specific ways users are using or want to use **Wispr Flow**
  - Each use case must have a direct quote from the TARGET COMMENT (not context)
  - Only extract if clearly about Wispr Flow (use thread context to determine)
  - Include both explicit and implicit use cases
  - **CRITICAL**: Break compound use cases into ATOMIC, SINGULAR actions
  - **IMPORTANT - Formatting**:
    - Keep use case text SHORT (2-5 words max)
    - Use gerund form (verb + -ing)
    - Focus on the ACTION

---

## Few-Shot Examples

### Example 1: Comment with Multiple Use Cases

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: What do you use Wispr Flow for?
Body: Curious what everyone's main use cases are

Community: r/WisprFlow
```

**TARGET COMMENT:**

```
I use it constantly for work. Mainly for writing emails to my team, taking notes during 1-on-1s, and dictating long prompts to ChatGPT when I'm coding. Game changer for productivity.
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "use_case": "Writing emails",
      "quote": "writing emails to my team"
    },
    {
      "use_case": "Taking notes in meetings",
      "quote": "taking notes during 1-on-1s"
    },
    {
      "use_case": "Prompting AI assistants",
      "quote": "dictating long prompts to ChatGPT when I'm coding"
    },
    {
      "use_case": "Vibe coding",
      "quote": "dictating long prompts to ChatGPT when I'm coding"
    }
  ]
}
```

**Why this output?**
- "Taking notes during 1-on-1s" → "Taking notes in meetings" (activity + context)
- "Dictating prompts to ChatGPT when coding" → "Prompting AI assistants" + "Vibe coding"
- All use cases are atomic and in gerund form

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
      "use_case": "Writing emails",
      "quote": "Right now I mainly use it for emails"
    }
  ]
}
```

**Why this output?**
- ✅ "Right now I mainly use it for emails" → CURRENT use case (they're doing it now)
- ❌ "better support for coding in Cursor" → SKIPPED (feature request, not current use)
- ❌ "could see it being useful for describing code" → SKIPPED (hypothetical)

---

### Example 3: ❌ BAD vs ✅ GOOD - Generic vs Specific

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

**❌ WRONG OUTPUT (DO NOT DO THIS):**

```json
{
  "use_cases": [
    {
      "use_case": "Dictating",
      "quote": "The dictation is incredible"
    },
    {
      "use_case": "Smart formatting",
      "quote": "Smart formatting works great"
    }
  ]
}
```

**Why this is WRONG:**
- "Dictating" is too generic - that's what the app does
- "Smart formatting" is a FEATURE, not a use case

**✅ CORRECT OUTPUT:**

```json
{
  "use_cases": []
}
```

**Why this is CORRECT:**
- Comment doesn't mention WHAT they're dictating or WHEN/WHERE
- Empty array is valid when no specific use cases are found

---

## Now Extract Use Cases from This Comment:

[THREAD CONTEXT AND TARGET COMMENT WILL BE PROVIDED HERE]
