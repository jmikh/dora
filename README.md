# Wispr Flow Complaints Dashboard

A visual dashboard for exploring and analyzing customer complaints.

---

## Before You Start

You'll need to use the **Terminal** app to run a few commands. Don't worry - we'll walk you through it step by step!

### How to Open Terminal on Mac

1. Press `Cmd + Space` to open Spotlight
2. Type `Terminal` and press Enter
3. A window with a command line will open

---

## Step 1: Navigate to the Project Folder

First, you need to tell Terminal where the project files are.

**Copy and paste this command into Terminal, then press Enter:**

```bash
cd ~/Projects/dora/demo_site
```

> **What this does:** `cd` means "change directory" - it's like opening a folder in Finder.

**To verify you're in the right place, run:**

```bash
ls
```

You should see files like `index.html`, `app.js`, and `generate_data.py`.

---

## Step 2: Generate the Data

Before viewing the dashboard, you need to generate the complaints data from the database.

**Run this command:**

```bash
python3 generate_data.py
```

> **What this does:** This script reads complaints from the database and creates a `data/complaints.json` file that the dashboard uses.

**If you see an error about missing OpenAI API key:**
1. Make sure you have a `.env` file in the main `dora` folder
2. The file should contain: `OPENAI_API_KEY=your_key_here`

---

## Step 3: Start the Dashboard Server

To view the dashboard in your browser, you need to start a local web server.

**Run this command:**

```bash
python3 -m http.server 8000
```

> **What this does:** This starts a mini web server on your computer so you can view the dashboard.

**You should see:**
```
Serving HTTP on :: port 8000 (http://[::]:8000/) ...
```

---

## Step 4: Open the Dashboard

1. Open your web browser (Chrome, Safari, Firefox, etc.)
2. Go to: **http://localhost:8000**
3. You should see the complaints dashboard!

---

## Step 5: Stopping the Server

When you're done using the dashboard:

1. Go back to the Terminal window
2. Press `Ctrl + C` (hold Control and press C)
3. The server will stop

---

## Quick Reference (All Commands)

Here's a summary you can copy/paste:

```bash
# 1. Go to the project folder
cd ~/Projects/dora/demo_site

# 2. Generate fresh data (if needed)
python3 generate_data.py

# 3. Start the server
python3 -m http.server 8000

# 4. Open in browser: http://localhost:8000

# 5. To stop: press Ctrl+C in Terminal
```

---

## Troubleshooting

### "command not found: python3"

You need to install Python. Run:
```bash
brew install python3
```

If you don't have Homebrew, first install it:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### "No such file or directory"

Make sure you're in the right folder. Run `pwd` to see where you are:
```bash
pwd
```

It should show something like `/Users/yourname/Projects/dora/demo_site`

### The dashboard shows no data

Make sure you ran `python3 generate_data.py` first and it completed without errors.

### "Address already in use"

Another server is already running on port 8000. Either:
- Find and close the other Terminal window running a server
- Or use a different port: `python3 -m http.server 8001` (then visit http://localhost:8001)

---

## Project Files

| File | What it does |
|------|--------------|
| `index.html` | The main dashboard page |
| `styles.css` | How the dashboard looks (colors, fonts, etc.) |
| `app.js` | The code that makes the dashboard interactive |
| `generate_data.py` | Creates the data file from the database |
| `data/complaints.json` | The complaints data (auto-generated) |
