import json
import os
from pathlib import Path

import litellm

from transcript_cli.models import EnrichedTranscript, RawTranscript

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load_prompt(name: str, **kwargs: str) -> str:
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
    if kwargs:
        text = text.format(**kwargs)
    return text


def _parse_response(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return json.loads(text)


def enrich(raw: RawTranscript, normalised_text: str) -> EnrichedTranscript:
    model = os.environ.get("TRANSCRIPT_MODEL")
    if not model:
        raise RuntimeError("TRANSCRIPT_MODEL not set. Add it to your .env file.")
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": _load_prompt("enrich")},
            {"role": "user", "content": normalised_text},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    parsed = _parse_response(response.choices[0].message.content)

    return EnrichedTranscript(
        raw=raw,
        clean_text=parsed.get("clean_text", normalised_text),
        summary=parsed.get("summary", ""),
        topics=parsed.get("topics", []),
        participants=parsed.get("participants", []),
    )
