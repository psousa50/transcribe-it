from pathlib import Path
from typing import Annotated

import questionary
import typer
import yaml

from transcript_cli.config import CONFIG_PATH
from transcript_cli.main import GLOBAL_ENV_PATH

app = typer.Typer(name="init", invoke_without_command=True)

ENV_PATH = GLOBAL_ENV_PATH

LLM_PROVIDERS = {
    "Anthropic (Claude)": ("anthropic/claude-sonnet-4-20250514", "ANTHROPIC_API_KEY"),
    "OpenAI (GPT-4o Mini)": ("openai/gpt-4o-mini", "OPENAI_API_KEY"),
    "Groq (Llama 3.3 70B)": ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY"),
}


def _prompt_gmail() -> tuple[dict, dict]:
    typer.echo("\nGmail configuration:")
    sender = questionary.text("Sender email to filter by (e.g. gemini-notes@google.com):").ask()
    profile = questionary.text("Auth profile name:", default="default").ask()
    typer.echo("\nGoogle OAuth client (ask a teammate for these values):")
    client_id = questionary.text("GOOGLE_OAUTH_CLIENT_ID:").ask()
    client_secret = questionary.password("GOOGLE_OAUTH_CLIENT_SECRET:").ask()
    env = {
        "GOOGLE_OAUTH_CLIENT_ID": client_id,
        "GOOGLE_OAUTH_CLIENT_SECRET": client_secret,
    }
    return {"profile": profile, "sender": sender}, env


def _prompt_slack() -> tuple[dict, dict]:
    typer.echo("\nSlack configuration:")
    typer.echo("(Find channel ID via: right-click channel -> View channel details)")
    channel = questionary.text("Channel ID (e.g. C01ABCDEF123):").ask()
    token = questionary.password("Slack bot token (starts with xoxb-):").ask()
    return {"channel": channel}, {"SLACK_BOT_TOKEN": token}


SOURCES = {
    "Gmail": ("gmail", _prompt_gmail),
    "Slack": ("slack", _prompt_slack),
}


def _read_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    values = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def _write_env(values: dict[str, str]) -> None:
    existing = _read_env()
    updates: dict[str, str] = {}

    for key, value in values.items():
        if not value:
            continue
        if key in existing:
            if existing[key] == value:
                continue
            if questionary.confirm(f"{key} already set in .env. Overwrite?", default=False).ask():
                updates[key] = value
        else:
            updates[key] = value

    if not updates:
        return

    if not ENV_PATH.exists():
        ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        ENV_PATH.write_text("")

    lines = ENV_PATH.read_text().splitlines()
    updated_keys: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n")


def _prompt_llm() -> dict[str, str]:
    typer.echo("\nLLM configuration:")
    provider_label = questionary.select(
        "Which LLM provider do you want to use?",
        choices=list(LLM_PROVIDERS.keys()),
    ).ask()
    model, key_name = LLM_PROVIDERS[provider_label]
    api_key = questionary.password(f"{key_name}:").ask()
    return {"TRANSCRIPT_MODEL": model, key_name: api_key}


def _print_next_steps(sources: list[str]) -> None:
    typer.echo("\nNext steps:")
    if "gmail" in sources:
        typer.echo("  - Authenticate with Gmail: transcript auth gmail")
    if "slack" in sources:
        typer.echo("  - Invite your Slack bot to the channels you want to ingest from")


@app.callback()
def init(
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing config")] = False,
) -> None:
    if CONFIG_PATH.exists() and not force:
        typer.echo(f"Config already exists at {CONFIG_PATH}. Use --force to overwrite.", err=True)
        raise typer.Exit(code=1)

    typer.echo("Initialising transcript config...\n")

    chosen_labels = questionary.checkbox(
        "Which sources do you want to enable?",
        choices=list(SOURCES.keys()),
    ).ask()

    if not chosen_labels:
        typer.echo("At least one source must be selected.", err=True)
        raise typer.Exit(code=1)

    sources: dict = {}
    selected = []
    env_updates: dict[str, str] = {}

    for label in chosen_labels:
        key, prompt_fn = SOURCES[label]
        source_config, source_env = prompt_fn()
        sources[key] = source_config
        env_updates.update(source_env)
        selected.append(key)

    env_updates.update(_prompt_llm())

    output_path = questionary.text("\nOutput directory for transcripts:", default=".transcripts/").ask()
    lookback_days = questionary.text("Default lookback period (days):", default="7").ask()

    config = {
        "sources": sources,
        "lookback_days": int(lookback_days),
        "destinations": [
            {"type": "local", "path": output_path},
        ],
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(yaml.safe_dump(config, sort_keys=False))
    typer.echo(f"\nConfig written to {CONFIG_PATH}")

    _write_env(env_updates)
    typer.echo(f"Environment variables written to {ENV_PATH}")

    _print_next_steps(selected)
