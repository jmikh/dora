# Reddit POST Value Driver Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **value drivers** about **Wispr Flow**, a voice-to-text dictation app, from Reddit posts. You will be given a single Reddit post (title + body) and need to extract WHY users love Wispr Flow.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "value_drivers": [
    {
      "value_driver": "Concise description of the benefit",
      "quote": "Exact quote from post"
    }
  ]
}
```

### Field Definitions:

- **value_driver**: A concise description of the benefit/value the user experiences (5-15 words)
- **quote**: Direct quote from the post supporting this value driver

### Rules:

- Only extract value drivers clearly about Wispr Flow
- Focus on WHY they love it, not WHAT they use it for
- Each value driver should describe a specific benefit
- Return empty array if no value drivers found

---

## Few-Shot Examples

### Example 1: Multiple Value Drivers

**POST:**

```
Title: Wispr Flow changed how I work
Body: I've been using Wispr Flow for 3 months and it's transformed my workflow. The speed is insane - I write emails 4x faster now. But what really gets me is how it cleans up my rambling into professional text. I just speak naturally and it formats everything perfectly. No more staring at a blank screen trying to find the right words.

Also, my wrist pain from years of typing has basically disappeared since I switched to voice.

Community: r/ProductivityApps
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "value_driver": "4x faster than typing for emails",
      "quote": "I write emails 4x faster now"
    },
    {
      "value_driver": "Transforms rambling speech into professional text",
      "quote": "it cleans up my rambling into professional text"
    },
    {
      "value_driver": "Automatic formatting without manual effort",
      "quote": "I just speak naturally and it formats everything perfectly"
    },
    {
      "value_driver": "Eliminates writer's block",
      "quote": "No more staring at a blank screen trying to find the right words"
    },
    {
      "value_driver": "Reduces wrist pain from typing",
      "quote": "my wrist pain from years of typing has basically disappeared"
    }
  ]
}
```

---

### Example 2: Use Cases vs Value Drivers

**POST:**

```
Title: Using Wispr for coding
Body: I use Wispr Flow with Cursor every day. The accuracy is incredible - it even gets my variable names right. I added them to my personal dictionary and now it never misses.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "value_driver": "High accuracy for technical terms and variable names",
      "quote": "The accuracy is incredible - it even gets my variable names right"
    },
    {
      "value_driver": "Personal dictionary learns custom vocabulary",
      "quote": "I added them to my personal dictionary and now it never misses"
    }
  ]
}
```

**Why this output?**
- ❌ "I use Wispr Flow with Cursor" → NOT extracted (that's a use case, not a value driver)
- ✅ "accuracy is incredible" → Extracted (that's WHY they love it)
- ✅ "personal dictionary" → Extracted (benefit of learning their vocabulary)

---

### Example 3: No Value Drivers

**POST:**

```
Title: Question about Wispr Flow
Body: Does Wispr Flow work on Windows? I'm thinking about trying it for my work emails.

Community: r/WisprFlow
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": []
}
```

**Why:** This is just a question, no value drivers expressed.

---

## Now Extract Value Drivers from This Post:

[POST WILL BE PROVIDED HERE]
