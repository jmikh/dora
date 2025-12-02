# Reddit COMMENT Value Driver Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **value drivers** about **Wispr Flow**, a voice-to-text dictation app, from Reddit comments. You will be given a comment with its full thread context and need to classify WHY users love Wispr Flow into predefined categories.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "value_drivers": [
    {
      "category": "productivity",
      "quote": "Exact quote from comment"
    }
  ]
}
```

For the `other` category, include a description:

```json
{
  "category": "other",
  "other_description": "Brief description",
  "quote": "Exact quote from comment"
}
```

### Field Definitions:

- **category**: One of: `productivity`, `speed`, `accuracy`, `reliability`, `ease_of_use`, `accessibility`, `formatting`, `contextual_understanding`, `universality`, `other`
- **other_description**: (Only for `other` category) Brief description of the value driver
- **quote**: Direct quote from the TARGET COMMENT (not context)

---

## Few-Shot Examples

### Example 1: Multiple Value Drivers

**THREAD CONTEXT:**

```
[POST - ROOT]
Title: Why do you use Wispr Flow?
Body: What made you switch to voice dictation?

Community: r/WisprFlow
```

**TARGET COMMENT:**

```
The speed difference is night and day. I can get through my inbox in half the time now. And it works in literally every app - no switching tools or copy-pasting. The transcription never misses a word either.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "productivity",
      "quote": "I can get through my inbox in half the time now"
    },
    {
      "category": "universality",
      "quote": "it works in literally every app - no switching tools or copy-pasting"
    },
    {
      "category": "accuracy",
      "quote": "The transcription never misses a word"
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
I use it mainly for Slack and email. What I love is that it just works - no setup, no fiddling. My messages come out way more professional than when I type.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "ease_of_use",
      "quote": "it just works - no setup, no fiddling"
    },
    {
      "category": "contextual_understanding",
      "quote": "My messages come out way more professional than when I type"
    }
  ]
}
```

**Why this output?**
- ❌ "I use it mainly for Slack and email" → NOT extracted (use case)
- ✅ "just works - no setup" → `ease_of_use`
- ✅ "more professional than when I type" → `contextual_understanding`

---

### Example 3: Accessibility Value Driver

**TARGET COMMENT:**

```
As someone with carpal tunnel, this has been life-changing. I can finally write all day without pain. It even understands my slight accent perfectly.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "accessibility",
      "quote": "I can finally write all day without pain"
    },
    {
      "category": "accuracy",
      "quote": "It even understands my slight accent perfectly"
    }
  ]
}
```

---

## Now Extract Value Drivers from This Comment:

[THREAD CONTEXT AND TARGET COMMENT WILL BE PROVIDED HERE]
