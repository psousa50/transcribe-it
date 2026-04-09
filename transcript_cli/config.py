from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class GmailSourceConfig:
    profile: str = "default"
    sender: str = ""


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


def load_config(project_root: Path | None = None) -> TranscriptConfig:
    root = project_root or Path.cwd()
    config_path = root / ".transcripts" / "config.yaml"

    if not config_path.exists():
        return TranscriptConfig()

    raw = yaml.safe_load(config_path.read_text()) or {}

    gmail_raw = raw.get("sources", {}).get("gmail", {})
    gmail = GmailSourceConfig(
        profile=gmail_raw.get("profile", "default"),
        sender=gmail_raw.get("sender", ""),
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
