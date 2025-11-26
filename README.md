# Wispr Flow Complaints Dashboard

A static analytics dashboard for visualizing and exploring customer complaints.

## Quick Start

### Using Python (recommended)

```bash
cd demo_site
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser.

### Using Node.js

```bash
npx serve demo_site
```

### Using PHP

```bash
cd demo_site
php -S localhost:8000
```

## Generating Data

Before running the dashboard, you need to generate the complaints data:

```bash
cd demo_site
python3 generate_data.py
```

This will:
1. Read complaints from the database (`../dora.db`)
2. Generate AI summaries for each category using OpenAI
3. Output data to `data/complaints.json`

### Requirements for data generation

- Python 3.8+
- OpenAI API key in `../.env` file:
  ```
  OPENAI_API_KEY=your_key_here
  ```

## Project Structure

```
demo_site/
├── index.html          # Main dashboard HTML
├── styles.css          # Styling
├── app.js              # Dashboard logic
├── generate_data.py    # Data generation script
├── data/
│   └── complaints.json # Generated data
└── icons/              # Platform icons
    ├── reddit.png
    ├── appstore.png
    ├── producthunt.png
    ├── trustpilot.png
    └── windows.png
```
