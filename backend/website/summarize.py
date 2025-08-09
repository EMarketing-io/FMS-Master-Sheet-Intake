import json
import re
from typing import Optional

import openai
from config import OPENAI_KEY, OPENAI_MODEL

# Configure once
openai.api_key = OPENAI_KEY


def _extract_balanced_json(text: str) -> Optional[str]:
    """Find the first balanced {...} block via brace counting."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _try_json_loads(s: str) -> dict:
    """Parse JSON with fallbacks to repair common model mistakes."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # If available, try json_repair
    try:
        from json_repair import repair_json  # optional dependency

        repaired = repair_json(s)
        return json.loads(repaired)
    except Exception:
        pass

    # Remove trailing commas before ] or }
    s2 = re.sub(r",(\s*[\]\}])", r"\1", s)

    # Escape unescaped double quotes inside values after a colon
    def _escape_inner_quotes(m: re.Match) -> str:
        prefix = m.group(1)  # includes :"
        body = m.group(2)  # string body
        body = re.sub(r'(?<!\\)"', r'\\"', body)
        return prefix + body + '"'

    s3 = re.sub(r'(:\s*")([^"]*?)"', _escape_inner_quotes, s2, flags=re.DOTALL)

    return json.loads(s3)


# 📊 Summarizes raw website content into a structured JSON using OpenAI GPT
def summarize_with_openai(webpage_text: str) -> dict:
    """
    Return structured JSON for a website page.
    - Enforces escaping of inner quotes in the prompt.
    - Uses robust extraction/repair; flow and schema unchanged.
    """
    prompt = f"""
You are a professional business analyst. Analyze the following website content and return **ONLY valid JSON**.

CRITICAL JSON RULES:
- Use double quotes for all JSON keys and string values.
- If you need to include quotes **inside** any string value, you **must escape** them as `\"`.
- Do **not** include backticks, code fences, markdown, or commentary — just the JSON object.
- Bold important keywords in content using `**bold**` (plain text inside JSON strings).
- Each "content" field must contain 4–6 bullet lines joined with `\\n`.

Use this exact schema:
{{
  "title": "<Website Title or Company Name>",
  "sections": [
    {{
      "heading": "Purpose",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }},
    {{
      "heading": "Target Audience",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }},
    {{
      "heading": "About the Company",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }},
    {{
      "heading": "Company Information",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }},
    {{
      "heading": "Unique Selling Proposition (USP)",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }},
    {{
      "heading": "Reviews/Testimonials",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }},
    {{
      "heading": "Products/Service Categories",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }},
    {{
      "heading": "Offers",
      "content": "- Bullet 1\\n- Bullet 2\\n- Bullet 3\\n- Bullet 4"
    }}
  ]
}}

Analyze this content:
\"\"\"{webpage_text}\"\"\"    
"""

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a careful data formatter who always returns valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        raw_text = response["choices"][0]["message"]["content"].strip().strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].lstrip()

        json_blob = _extract_balanced_json(raw_text) or raw_text
        parsed = _try_json_loads(json_blob)

        if not isinstance(parsed, dict):
            raise ValueError("Model did not return a JSON object.")

        parsed.setdefault("title", "Website Summary")
        parsed.setdefault("sections", [])
        return parsed

    except Exception as e:
        print("⚠️ OpenAI JSON parsing failed:", e)
        print("⚠️ Raw output was:\n", locals().get("raw_text", "N/A"))
        return {
            "title": "Summary Unavailable",
            "sections": [
                {
                    "heading": "Error",
                    "content": "OpenAI returned invalid or incomplete JSON. The system attempted auto-repair but failed.",
                }
            ],
        }
