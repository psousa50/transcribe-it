from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class GmailSourceConfig:
    profile: str = "default"
    sender: str = ""
    subjects: list[str] = field(default_factory=list)


@dataclass
class SlackSourceConfig:
    channel: str = ""


@dataclass
class LocalDestinationConfig:
    path: str = ".transcripts/"


@dataclass
class TranscriptConfig:
    lookback_days: int = 7
    gmail: GmailSourceConfig = field(default_factory=GmailSourceConfig)
    slack: SlackSourceConfig = field(default_factory=SlackSourceConfig)
    local: LocalDestinationConfig = field(default_factory=LocalDestinationConfig)


CONFIG_PATH = Path(".transcripts/config.yaml")


def _as_patterns(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        value = [value]
    return [p.strip() for p in value if str(p).strip()]


def load_config(project_root: Path | None = None) -> TranscriptConfig:
    root = project_root or Path.cwd()
    config_path = root / CONFIG_PATH

    if not config_path.exists():
        return TranscriptConfig()

    raw = yaml.safe_load(config_path.read_text()) or {}

    gmail_raw = raw.get("sources", {}).get("gmail", {})
    gmail = GmailSourceConfig(
        profile=gmail_raw.get("profile", "default"),
        sender=gmail_raw.get("sender", ""),
        subjects=_as_patterns(gmail_raw.get("subject")),
    )

    destinations = raw.get("destinations", [])
    local_path = ".transcripts/"
    for dest in destinations:
        if dest.get("type") == "local":
            local_path = dest.get("path", local_path)
            break

    slack_raw = raw.get("sources", {}).get("slack", {})
    slack = SlackSourceConfig(
        channel=slack_raw.get("channel", ""),
    )

    return TranscriptConfig(
        lookback_days=raw.get("lookback_days", 7),
        gmail=gmail,
        slack=slack,
        local=LocalDestinationConfig(path=local_path),
    )
