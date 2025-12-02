# Reddit POST Value Driver Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **value drivers** about **Wispr Flow**, a voice-to-text dictation app, from Reddit posts. You will be given a single Reddit post and need to classify WHY users love Wispr Flow into predefined categories.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "value_drivers": [
    {
      "category": "productivity",
      "quote": "Exact quote from post"
    }
  ]
}
```

For the `other` category, include a description:

```json
{
  "category": "other",
  "other_description": "Helps with creative writing flow",
  "quote": "Exact quote from post"
}
```

### Field Definitions:

- **category**: One of: `productivity`, `speed`, `accuracy`, `reliability`, `ease_of_use`, `accessibility`, `formatting`, `contextual_understanding`, `universality`, `other`
- **other_description**: (Only for `other` category) Brief description of the value driver
- **quote**: Direct quote from the post supporting this value driver

---

## Few-Shot Examples

### Example 1: Multiple Value Drivers

**POST:**

```
Title: Wispr Flow changed how I work
Body: I've been using Wispr Flow for 3 months and it's transformed my workflow. I write emails 4x faster now. The transcription is incredibly accurate - it even gets technical terms right. What really gets me is how it cleans up my rambling into professional text. I just speak naturally and it formats everything perfectly with proper punctuation and paragraphs.

Also, my wrist pain from years of typing has basically disappeared.

Community: r/ProductivityApps
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "productivity",
      "quote": "I write emails 4x faster now"
    },
    {
      "category": "accuracy",
      "quote": "The transcription is incredibly accurate - it even gets technical terms right"
    },
    {
      "category": "contextual_understanding",
      "quote": "it cleans up my rambling into professional text"
    },
    {
      "category": "formatting",
      "quote": "it formats everything perfectly with proper punctuation and paragraphs"
    },
    {
      "category": "accessibility",
      "quote": "my wrist pain from years of typing has basically disappeared"
    }
  ]
}
```

---

### Example 2: Use Case vs Value Driver

**POST:**

```
Title: Using Wispr for coding
Body: I use Wispr Flow with Cursor every day. The accuracy is incredible - it gets my variable names right. It works in literally every app which is amazing.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "accuracy",
      "quote": "The accuracy is incredible - it gets my variable names right"
    },
    {
      "category": "universality",
      "quote": "It works in literally every app"
    }
  ]
}
```

**Why this output?**
- ❌ "I use Wispr Flow with Cursor" → NOT extracted (use case, not value driver)
- ✅ "accuracy is incredible" → Extracted (WHY they love it)

---

### Example 3: No Value Drivers

**POST:**

```
Title: Question about Wispr
Body: Does Wispr Flow work on Windows? I'm thinking about trying it.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": []
}
```

---

## Now Extract Value Drivers from This Post:

[POST WILL BE PROVIDED HERE]
