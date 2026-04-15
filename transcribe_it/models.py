from dataclasses import dataclass, field
from datetime import date


@dataclass
class RawTranscript:
    text: str
    source: str
    date: date
    source_id: str | None = None
    title: str | None = None


@dataclass
class EnrichedTranscript:
    raw: RawTranscript
    clean_text: str
    summary: str
    topics: list[str] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
