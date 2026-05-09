import json
import os
from datetime import date

from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are an Email Summarization Agent.

Your job:
1. Summarize the email in 2–3 sentences
2. Extract key points
3. Extract action items (who should do what)
4. Identify deadlines
5. Classify urgency: Low, Medium, or High

Return ONLY valid JSON with this exact schema:
{
  "summary": "",
  "key_points": [],
  "action_items": [{"who": "", "what": ""}],
  "deadlines": [],
  "urgency": ""
}"""


def read_email(path: str = "email.txt") -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_email(email_text: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": email_text},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def save_outputs(data: dict) -> None:
    with open("summary.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(f"Email Summary ({date.today()})\n")
        f.write("=" * 40 + "\n\n")
        f.write("SUMMARY:\n")
        f.write(data["summary"] + "\n\n")

        f.write("KEY POINTS:\n")
        for point in data["key_points"]:
            f.write(f"- {point}\n")

        f.write("\nACTION ITEMS:\n")
        for action in data["action_items"]:
            if isinstance(action, dict):
                who = action.get("who") or action.get("assignee", "")
                what = action.get("what") or action.get("task", "")
                f.write(f"- {who}: {what}\n")
            else:
                f.write(f"- {action}\n")

        f.write("\nDEADLINES:\n")
        for deadline in data["deadlines"]:
            f.write(f"- {deadline}\n")

        f.write(f"\nURGENCY: {data['urgency']}\n")


def main() -> None:
    email_text = read_email()
    result = summarize_email(email_text)
    save_outputs(result)
    print("Email summarized successfully.")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
