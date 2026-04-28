from typing import Annotated

import questionary
import typer
import yaml

from transcribe_it.commands.setup import read_env
from transcribe_it.config import CONFIG_PATH

app = typer.Typer(name="init", invoke_without_command=True)

REQUIRED_ENV = {
    "gmail": ["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
    "slack": ["SLACK_BOT_TOKEN"],
}


def _prompt_gmail() -> dict:
    typer.echo("\nGmail configuration:")
    sender = questionary.text("Sender email to filter by (e.g. gemini-notes@google.com):").ask()
    profile = questionary.text("Auth profile name:", default="default").ask()
    return {"profile": profile, "sender": sender}


def _prompt_slack() -> dict:
    typer.echo("\nSlack configuration:")
    typer.echo("(Find channel ID via: right-click channel -> View channel details)")
    channel = questionary.text("Channel ID (e.g. C01ABCDEF123):").ask()
    return {"channel": channel}


SOURCES = {
    "Gmail": ("gmail", _prompt_gmail),
    "Slack": ("slack", _prompt_slack),
}


def _warn_missing_env(selected_sources: list[str]) -> None:
    env = read_env()
    missing: list[str] = []
    for source in selected_sources:
        for key in REQUIRED_ENV.get(source, []):
            if not env.get(key):
                missing.append(key)
    if missing:
        typer.echo(
            f"\nWarning: missing credentials in env: {', '.join(missing)}.\n"
            "Run `transcribe-it setup` to configure them before ingesting.",
            err=True,
        )


def _print_next_steps(sources: list[str]) -> None:
    typer.echo("\nNext steps:")
    if "gmail" in sources:
        typer.echo("  - Authenticate with Gmail: transcribe-it auth gmail")
    if "slack" in sources:
        typer.echo("  - Invite your Slack bot to the channels you want to ingest from")


@app.callback()
def init(
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing config")] = False,
) -> None:
    if CONFIG_PATH.exists() and not force:
        typer.echo(f"Config already exists at {CONFIG_PATH}. Use --force to overwrite.", err=True)
        raise typer.Exit(code=1)

    typer.echo("Initialising project config...\n")

    chosen_labels = questionary.checkbox(
        "Which sources do you want to enable?",
        choices=list(SOURCES.keys()),
    ).ask()

    if not chosen_labels:
        typer.echo("At least one source must be selected.", err=True)
        raise typer.Exit(code=1)

    sources: dict = {}
    selected: list[str] = []

    for label in chosen_labels:
        key, prompt_fn = SOURCES[label]
        sources[key] = prompt_fn()
        selected.append(key)

    output_path = questionary.text("\nOutput directory for transcripts:", default="transcripts/").ask()
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

    _warn_missing_env(selected)
    _print_next_steps(selected)
