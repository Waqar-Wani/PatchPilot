import json
from json import JSONDecodeError
from openai import OpenAI
from config import OPENROUTER_KEY, OPENROUTER_MODEL, OPENROUTER_BASE

# Validate critical config early to avoid None.encode crashes in the client
if not OPENROUTER_KEY or str(OPENROUTER_KEY).strip() == "":
    raise ValueError("OPENROUTER_API_KEY is missing; set it in .env")
if not OPENROUTER_BASE or str(OPENROUTER_BASE).strip() == "":
    raise ValueError("OPENROUTER_BASE is missing; set it in .env")

# OpenAI-compatible client pointed at OpenRouter
client = OpenAI(api_key=OPENROUTER_KEY, base_url=OPENROUTER_BASE)

SYSTEM_PROMPT = open("patchpilot_prompt.txt").read()


def _parse_json_content(content: str) -> dict:
    """Best-effort JSON parsing that tolerates fenced code blocks and trailing text."""
    text = content.strip()
    if text.startswith("```"):
        # Drop leading/trailing code fences if present
        lines = text.splitlines()
        if len(lines) >= 2:
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except JSONDecodeError:
        # Try to salvage first JSON object inside the text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except JSONDecodeError:
                pass
        # As a last resort, return raw for debugging
        return {"raw_response": text}


def analyze_repo(snapshot: dict) -> dict:
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        max_tokens=2000,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(snapshot)}
        ],
    )
    content = response.choices[0].message.content or ""
    return _parse_json_content(content)
