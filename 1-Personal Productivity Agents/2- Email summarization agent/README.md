# Email Summarization Agent

An AI-powered agent that reads an email and extracts a structured summary, key points, action items, deadlines, and urgency level. Built as **Day 2 of 100 AI Agents in 100 Days 2026**.

<img width="332" height="402" alt="image" src="https://github.com/user-attachments/assets/77884655-6fa3-47fe-83b4-2669d515a0c7" />

## Features

- Summarizes any email in 2–3 sentences
- Extracts key points, action items, and deadlines
- Classifies urgency as Low, Medium, or High
- Outputs results to `summary.json` and `summary.txt`
- Two modes: CLI and Streamlit web UI

## Tech Stack

- **LLM:** Llama 3.3 70B via [Groq](https://console.groq.com) (free)
- **UI:** Streamlit
- **Language:** Python 3.10+

## Project Structure

```
Email Summarization Agent/
├── agent.py        # Core logic: reads email, calls LLM, saves outputs
├── app.py          # Streamlit web UI
├── email.txt       # Input email
├── summary.json    # Output: structured JSON
└── summary.txt     # Output: human-readable summary
```

## Setup

### 1. Install dependencies

```bash
pip install groq streamlit
```

### 2. Get a free Groq API key

Sign up at [console.groq.com](https://console.groq.com) → API Keys → Create API Key.

### 3. Set your API key

```powershell
$env:GROQ_API_KEY = "your-key-here"
```

## Usage

### CLI mode

Add your email content to `email.txt`, then run:

```bash
python agent.py
```

Outputs are saved to `summary.json` and `summary.txt`.

### Web UI mode

```bash
streamlit run app.py
```

Opens in your browser at `http://localhost:8501`. Paste any email and click **Summarize Email**.

## Example Output

**Input** (`email.txt`):
```
Subject: Project Timeline Update

The client has requested that the initial prototype be delivered by March 10.
Design needs to finalize assets by March 5. Engineering should prioritize API integration.
```

**Output** (`summary.json`):
```json
{
  "summary": "The Q1 project timeline has been updated with a new prototype delivery date of March 10.",
  "key_points": [
    "Prototype delivery date changed to March 10",
    "Design assets must be finalized by March 5",
    "Engineering to prioritize API integration"
  ],
  "action_items": [
    { "who": "Design team", "what": "Finalize assets by March 5" },
    { "who": "Engineering team", "what": "Prioritize API integration" }
  ],
  "deadlines": ["March 5", "March 10"],
  "urgency": "Medium"
}
```
