# Reddit COMMENT Value Driver Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **value drivers** about **Wispr Flow**, a voice-to-text dictation app, from Reddit comments. You will be given a comment with its full thread context and need to extract WHY users love Wispr Flow.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "value_drivers": [
    {
      "value_driver": "Concise description of the benefit",
      "quote": "Exact quote from comment"
    }
  ]
}
```

### Field Definitions:

- **value_driver**: A concise description of the benefit/value the user experiences (5-15 words)
- **quote**: Direct quote from the TARGET COMMENT (not context)

### Rules:

- Only extract from the TARGET COMMENT, not the context
- Focus on WHY they love it, not WHAT they use it for
- Each value driver should describe a specific benefit
- Return empty array if no value drivers found

---

## Few-Shot Examples

### Example 1: Comment with Value Drivers

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Why do you use Wispr Flow?
Body: What made you switch to voice dictation?

Community: r/WisprFlow
```

**TARGET COMMENT:**

```
Honestly, the speed difference is night and day. I can get through my inbox in half the time now. And the fact that it works in literally every app means I don't have to switch tools or copy-paste anything.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "value_driver": "Dramatically faster email processing",
      "quote": "I can get through my inbox in half the time now"
    },
    {
      "value_driver": "Works universally in all apps without switching tools",
      "quote": "it works in literally every app means I don't have to switch tools or copy-paste anything"
    }
  ]
}
```

---

### Example 2: Use Case vs Value Driver

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Wispr Flow users, check in!
Body: How's everyone using it?

Community: r/WisprFlow
```

**TARGET COMMENT:**

```
I use it mainly for Slack and email. What I love is that I sound way more articulate than when I type. My messages come out clearer and more professional.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "value_driver": "Makes user sound more articulate than typing",
      "quote": "I sound way more articulate than when I type"
    },
    {
      "value_driver": "Produces clearer, more professional messages",
      "quote": "My messages come out clearer and more professional"
    }
  ]
}
```

**Why this output?**
- ❌ "I use it mainly for Slack and email" → NOT extracted (use case)
- ✅ "sound way more articulate" → Extracted (value driver)

---

## Now Extract Value Drivers from This Comment:

[THREAD CONTEXT AND TARGET COMMENT WILL BE PROVIDED HERE]
