from typing import Annotated

import questionary
import typer

from transcribe_it.main import GLOBAL_ENV_PATH

app = typer.Typer(name="setup", invoke_without_command=True)

ENV_PATH = GLOBAL_ENV_PATH

LLM_PROVIDERS = {
    "Anthropic (Claude)": ("anthropic/claude-sonnet-4-20250514", "ANTHROPIC_API_KEY"),
    "OpenAI (GPT-4o Mini)": ("openai/gpt-4o-mini", "OPENAI_API_KEY"),
    "Groq (Llama 3.3 70B)": ("groq/llama-3.3-70b-versatile", "GROQ_API_KEY"),
}

CREDENTIAL_GROUPS = {
    "Google OAuth (Gmail source)": "google",
    "Slack bot token (Slack source)": "slack",
    "LLM provider (for --enrich)": "llm",
}


def read_env() -> dict[str, str]:
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


def write_env(values: dict[str, str], force: bool = False) -> None:
    existing = read_env()
    updates: dict[str, str] = {}

    for key, value in values.items():
        if not value:
            continue
        if key in existing and existing[key] == value:
            continue
        if key in existing and not force:
            if not questionary.confirm(f"{key} already set in {ENV_PATH}. Overwrite?", default=False).ask():
                continue
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


def _prompt_google() -> dict[str, str]:
    typer.echo("\nGoogle OAuth client (ask a teammate or create one in Google Cloud Console):")
    client_id = questionary.text("GOOGLE_OAUTH_CLIENT_ID:").ask()
    client_secret = questionary.password("GOOGLE_OAUTH_CLIENT_SECRET:").ask()
    return {
        "GOOGLE_OAUTH_CLIENT_ID": client_id,
        "GOOGLE_OAUTH_CLIENT_SECRET": client_secret,
    }


def _prompt_slack() -> dict[str, str]:
    typer.echo("\nSlack bot token:")
    token = questionary.password("SLACK_BOT_TOKEN (starts with xoxb-):").ask()
    return {"SLACK_BOT_TOKEN": token}


def _prompt_llm() -> dict[str, str]:
    typer.echo("\nLLM provider:")
    provider_label = questionary.select(
        "Which LLM provider do you want to use?",
        choices=list(LLM_PROVIDERS.keys()),
    ).ask()
    model, key_name = LLM_PROVIDERS[provider_label]
    api_key = questionary.password(f"{key_name}:").ask()
    return {"TRANSCRIPT_MODEL": model, key_name: api_key}


PROMPTS = {
    "google": _prompt_google,
    "slack": _prompt_slack,
    "llm": _prompt_llm,
}


@app.callback()
def setup(
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing values without prompting")] = False,
) -> None:
    typer.echo(f"Configuring credentials in {ENV_PATH}\n")

    chosen_labels = questionary.checkbox(
        "Which credentials do you want to set up?",
        choices=list(CREDENTIAL_GROUPS.keys()),
    ).ask()

    if not chosen_labels:
        typer.echo("Nothing selected.")
        return

    env_updates: dict[str, str] = {}
    for label in chosen_labels:
        env_updates.update(PROMPTS[CREDENTIAL_GROUPS[label]]())

    write_env(env_updates, force=force)
    typer.echo(f"\nCredentials written to {ENV_PATH}")
