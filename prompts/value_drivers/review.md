# Review Value Driver Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **value drivers** about **Wispr Flow**, a voice-to-text dictation app, from app store reviews. You will be given a single review and need to extract WHY users love Wispr Flow.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "value_drivers": [
    {
      "value_driver": "Concise description of the benefit",
      "quote": "Exact quote from review"
    }
  ]
}
```

### Field Definitions:

- **value_driver**: A concise description of the benefit/value the user experiences (5-15 words)
- **quote**: Direct quote from the review supporting this value driver

### Rules:

- Focus on WHY they love it, not WHAT they use it for
- Each value driver should describe a specific benefit
- Return empty array if no value drivers found

---

## Few-Shot Examples

### Example 1: Multiple Value Drivers

**REVIEW:**

```
Rating: 5 stars
Review: This app has saved me so much time. I used to spend 30 minutes writing emails, now it takes 5. The AI formatting is magical - I just ramble and it comes out perfect. Best purchase I've made this year.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "value_driver": "Reduces email writing time from 30 minutes to 5",
      "quote": "I used to spend 30 minutes writing emails, now it takes 5"
    },
    {
      "value_driver": "AI automatically formats rambling into polished text",
      "quote": "I just ramble and it comes out perfect"
    }
  ]
}
```

---

### Example 2: Accessibility Value Driver

**REVIEW:**

```
Rating: 5 stars
Review: As someone with carpal tunnel, this app has been life-changing. I can finally write without pain. The accuracy is also surprisingly good - it gets my medical terminology right.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "value_driver": "Enables pain-free writing for carpal tunnel sufferers",
      "quote": "I can finally write without pain"
    },
    {
      "value_driver": "Accurate transcription of medical terminology",
      "quote": "it gets my medical terminology right"
    }
  ]
}
```

---

### Example 3: Generic Praise (No Specific Value Drivers)

**REVIEW:**

```
Rating: 5 stars
Review: Great app! Love it! Highly recommend to everyone.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": []
}
```

**Why:** Generic praise without specific benefits stated.

---

## Now Extract Value Drivers from This Review:

[REVIEW WILL BE PROVIDED HERE]
