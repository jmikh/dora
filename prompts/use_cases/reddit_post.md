# Reddit POST Use Case Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **use cases** about **Wispr Flow**, a voice-to-text dictation app, from Reddit posts. You will be given a single Reddit post (title + body) and need to extract how users are using or want to use Wispr Flow.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "use_cases": [
    {
      "use_case": "Writing emails",
      "quote": "Exact quote from post"
    }
  ]
}
```

### Field Definitions:

- **use_cases**: List of specific ways users are using or want to use **Wispr Flow**
  - Each use case must have a direct quote from the post
  - Only extract if clearly about Wispr Flow (use subreddit/context to determine)
  - If post is in r/WisprFlow or clearly discussing Wispr, extract use cases even without explicit "Wispr" mentions
  - Include both explicit use cases ("I use it for X") and implicit ones ("It would be great for Y" → use case: "Y")
  - **CRITICAL**: Break compound use cases into ATOMIC, SINGULAR actions
    - ❌ "Sending emails while driving" → ✅ ["Writing emails", "Dictating while driving"]
  - **IMPORTANT - Formatting**:
    - Keep use case text SHORT (2-5 words max)
    - Use gerund form (verb + -ing): "Writing emails", "Taking notes"
    - Use simple, jargon-free language
    - Remove app name (don't say "Wispr Flow")
    - Focus on the ACTION, not the tool

---

## Few-Shot Examples

### Example 1: Multiple Use Cases

**POST:**

```
Title: Wispr Flow boosted my productivity 10x
Body: I've been using Wispr Flow for a few months now and it's been incredible. I mainly use it for:

1. Writing long emails to clients - way faster than typing
2. Taking meeting notes while on Zoom calls
3. Dictating prompts to ChatGPT and Claude for coding help
4. Sending quick Slack messages while I'm cooking dinner

The AI formatting is spot on for emails. I can just ramble and it makes it sound professional.

Community: r/ProductivityApps
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "use_case": "Writing emails",
      "quote": "Writing long emails to clients - way faster than typing"
    },
    {
      "use_case": "Taking notes in meetings",
      "quote": "Taking meeting notes while on Zoom calls"
    },
    {
      "use_case": "Prompting AI assistants",
      "quote": "Dictating prompts to ChatGPT and Claude for coding help"
    },
    {
      "use_case": "Vibe coding",
      "quote": "Dictating prompts to ChatGPT and Claude for coding help"
    },
    {
      "use_case": "Sending Slack messages",
      "quote": "Sending quick Slack messages while I'm cooking dinner"
    },
    {
      "use_case": "Multitasking while cooking",
      "quote": "Sending quick Slack messages while I'm cooking dinner"
    }
  ]
}
```

**Why this output?**
- "Taking meeting notes while on Zoom" → "Taking notes in meetings" (activity + context)
- "Dictating prompts to ChatGPT for coding" → "Prompting AI assistants" + "Vibe coding"
- "Sending Slack while cooking" → "Sending Slack messages" + "Multitasking while cooking"
- Use cases are atomic, specific, and in gerund form

---

### Example 2: Only CURRENT Use Cases (Skip Hypotheticals)

**POST:**

```
Title: Feature request: Better support for coding
Body: Would love to see better support for describing code to AI assistants like Cursor and Windsurf. Right now I use it for brain dumping ideas into Notion and writing emails, but I think it could be amazing for vibe coding.

Also, it would be great if it worked better while I'm driving. Sometimes I get ideas on my commute and want to capture them.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "use_cases": [
    {
      "use_case": "Taking notes in Notion",
      "quote": "brain dumping ideas into Notion"
    },
    {
      "use_case": "Writing emails",
      "quote": "writing emails"
    }
  ]
}
```

**Why this output?**
- ✅ "brain dumping ideas into Notion" → CURRENT use case (they're doing it now)
- ✅ "writing emails" → CURRENT use case (they're doing it now)
- ❌ "better support for coding" → SKIPPED (feature request, not current use)
- ❌ "it would be great if it worked better while I'm driving" → SKIPPED (hypothetical/wishful)
- ❌ "I get ideas on my commute and want to capture them" → SKIPPED (wishful, not actually doing it)

---

### Example 3: ❌ BAD vs ✅ GOOD - Generic Features vs Specific Use Cases

**POST:**

```
Title: This app is a game changer!
Body: The dictation is so accurate and the smart formatting feature is incredible. Voice typing has never been this good!

Community: r/WisprFlow
```

**❌ WRONG OUTPUT (DO NOT DO THIS):**

```json
{
  "use_cases": [
    {
      "use_case": "Dictating",
      "quote": "The dictation is so accurate"
    },
    {
      "use_case": "Smart formatting",
      "quote": "the smart formatting feature is incredible"
    },
    {
      "use_case": "Voice typing",
      "quote": "Voice typing has never been this good"
    }
  ]
}
```

**Why this is WRONG:**
- All three are FEATURES/CAPABILITIES, not use cases
- Doesn't tell us WHAT the user dictates or WHEN/WHERE
- "Dictating" without context is just describing what Wispr does

**✅ CORRECT OUTPUT:**

```json
{
  "use_cases": []
}
```

**Why this is CORRECT:**
- Post only praises features/capabilities
- No mention of actual activities (emails, notes, code, etc.)
- No mention of contexts (meetings, driving, walking, etc.)
- Empty use_cases array is valid when no real use cases found

**Remember**: We want to understand HOW and WHY people use Wispr, not just that they like the features!

---

## Now Extract Use Cases from This Post:

[POST WILL BE PROVIDED HERE]
