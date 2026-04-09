import json
import re
from pathlib import Path

from transcript_cli.models import EnrichedTranscript


class DuplicateTranscriptError(Exception):
    pass


def _slugify(title: str | None, max_length: int = 50) -> str:
    text = (title or "untitled").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_length].rstrip("-")


def _build_clean_md(transcript: EnrichedTranscript) -> str:
    title = transcript.raw.title or "Untitled"
    lines = [
        f"# {title}",
        "",
        "## Summary",
        transcript.summary,
        "",
        "## Topics",
    ]
    for topic in transcript.topics:
        lines.append(f"- {topic}")
    lines += [
        "",
        "## Transcript",
        transcript.clean_text,
    ]
    return "\n".join(lines) + "\n"


def _build_metadata(transcript: EnrichedTranscript) -> dict:
    return {
        "source": transcript.raw.source,
        "date": transcript.raw.date.isoformat(),
        "participants": transcript.participants,
        "topics": transcript.topics,
        "source_id": transcript.raw.source_id,
    }


def is_duplicate(base_path: Path, source_id: str) -> bool:
    if not base_path.exists():
        return False
    for metadata_file in base_path.rglob("metadata.json"):
        raw = json.loads(metadata_file.read_text(encoding="utf-8"))
        if raw.get("source_id") == source_id:
            return True
    return False


def persist(transcript: EnrichedTranscript, base_path: Path) -> Path:
    source_id = transcript.raw.source_id
    if source_id is not None and is_duplicate(base_path, source_id):
        raise DuplicateTranscriptError(
            f"Transcript with source_id '{source_id}' already exists"
        )

    slug = _slugify(transcript.raw.title)
    date_str = transcript.raw.date.isoformat()
    output_dir = base_path / f"{date_str}-{slug}"
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "raw.txt").write_text(transcript.raw.text, encoding="utf-8")
    (output_dir / "clean.md").write_text(_build_clean_md(transcript), encoding="utf-8")
    (output_dir / "metadata.json").write_text(
        json.dumps(_build_metadata(transcript), indent=2) + "\n",
        encoding="utf-8",
    )

    return output_dir
