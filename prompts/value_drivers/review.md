# Review Value Driver Extraction Prompt for Wispr Flow

## Your Task

You are an expert analyst extracting **value drivers** about **Wispr Flow**, a voice-to-text dictation app, from app store reviews. You will be given a single review and need to classify WHY users love Wispr Flow into predefined categories.

{{COMMON_RULES}}

## Output Schema

Return a JSON object with the following structure:

```json
{
  "value_drivers": [
    {
      "category": "productivity",
      "quote": "Exact quote from review"
    }
  ]
}
```

For the `other` category, include a description:

```json
{
  "category": "other",
  "other_description": "Brief description",
  "quote": "Exact quote from review"
}
```

### Field Definitions:

- **category**: One of: `productivity`, `speed`, `accuracy`, `reliability`, `ease_of_use`, `accessibility`, `formatting`, `contextual_understanding`, `universality`, `other`
- **other_description**: (Only for `other` category) Brief description of the value driver
- **quote**: Direct quote from the review supporting this value driver

---

## Few-Shot Examples

### Example 1: Multiple Value Drivers

**REVIEW:**

```
Rating: 5 stars
Review: This app has saved me so much time. I used to spend 30 minutes writing emails, now it takes 5. The transcription is instant - no lag at all. I just ramble and it comes out perfectly formatted with proper punctuation.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "productivity",
      "quote": "I used to spend 30 minutes writing emails, now it takes 5"
    },
    {
      "category": "speed",
      "quote": "The transcription is instant - no lag at all"
    },
    {
      "category": "formatting",
      "quote": "it comes out perfectly formatted with proper punctuation"
    }
  ]
}
```

---

### Example 2: Accessibility + Accuracy

**REVIEW:**

```
Rating: 5 stars
Review: As someone with carpal tunnel, this app is a lifesaver. I can finally write without pain. The accuracy is also surprisingly good - it gets my medical terminology right every time.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "accessibility",
      "quote": "I can finally write without pain"
    },
    {
      "category": "accuracy",
      "quote": "it gets my medical terminology right every time"
    }
  ]
}
```

---

### Example 3: Ease of Use + Reliability

**REVIEW:**

```
Rating: 5 stars
Review: Super easy to set up - took like 2 minutes. It just works, every single time. Never had a crash or glitch. Works perfectly in all my apps.
```

**CORRECT OUTPUT:**

```json
{
  "value_drivers": [
    {
      "category": "ease_of_use",
      "quote": "Super easy to set up - took like 2 minutes"
    },
    {
      "category": "reliability",
      "quote": "It just works, every single time. Never had a crash or glitch"
    },
    {
      "category": "universality",
      "quote": "Works perfectly in all my apps"
    }
  ]
}
```

---

### Example 4: Generic Praise (No Value Drivers)

**REVIEW:**

```
Rating: 5 stars
Review: Great app! Love it! Highly recommend.
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
