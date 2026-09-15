import hashlib
import subprocess
from dataclasses import replace
from datetime import date
from typing import Annotated

import typer

from transcribe_it.config import GmailSourceConfig, load_config
from transcribe_it.models import RawTranscript
from transcribe_it.pipeline.run import run
from transcribe_it.sources.gmail import build_query, fetch_transcripts, list_emails
from transcribe_it.sources.slack import fetch_transcripts as slack_fetch, list_files as slack_list

app = typer.Typer(name="ingest", no_args_is_help=True)


def _resolve_dates(date_from, date_to):
    parsed_from = date.fromisoformat(date_from) if date_from else None
    parsed_to = date.fromisoformat(date_to) if date_to else None
    return parsed_from, parsed_to


def _date_label(date_from, date_to, days):
    if date_from or date_to:
        return f"{date_from or '...'} to {date_to or '...'}"
    return f"last {days} day(s)"


def _select_accounts(accounts: list[GmailSourceConfig], profile: str | None) -> list[GmailSourceConfig]:
    if not profile:
        return accounts
    matching = [a for a in accounts if a.profile == profile]
    return matching or [replace(accounts[0], profile=profile)]


@app.command()
def gmail(
    profile: Annotated[str | None, typer.Option(help="Restrict the run to one Gmail account (default: all configured)")] = None,
    days: Annotated[int | None, typer.Option(help="How many days back to search")] = None,
    date_from: Annotated[str | None, typer.Option("--from", help="Start date (YYYY-MM-DD)")] = None,
    date_to: Annotated[str | None, typer.Option("--to", help="End date (YYYY-MM-DD)")] = None,
    subject: Annotated[list[str] | None, typer.Option(help="Subject filter; repeatable, * and ? wildcards, overrides config")] = None,
    enrich: Annotated[bool, typer.Option("--enrich", help="Run LLM enrichment (summary, topics, participants)")] = False,
    clean: Annotated[bool, typer.Option("--clean", help="Also generate a cleaned version of the transcript (implies --enrich)")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    config = load_config()
    accounts = _select_accounts(config.gmail, profile)
    parsed_from, parsed_to = _resolve_dates(date_from, date_to)
    resolved_days = days or config.lookback_days
    label = _date_label(date_from, date_to, resolved_days)

    unconfigured = [a.profile for a in accounts if not a.sender]
    if unconfigured:
        typer.echo(
            f"Error: No Gmail sender configured for profile(s) {', '.join(unconfigured)}. "
            "Set sources.gmail.sender in .transcripts/config.yaml.",
            err=True,
        )
        raise typer.Exit(code=1)

    found: list[tuple[GmailSourceConfig, list]] = []
    for account in accounts:
        subjects = list(subject) if subject else account.subjects
        query = build_query(account.sender, resolved_days, date_from=parsed_from, date_to=parsed_to, subjects=subjects)
        typer.echo(f"Searching emails with profile '{account.profile}' ({label})...")

        try:
            matches = list_emails(profile=account.profile, query=query, subject_filters=subjects)
        except FileNotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

        if matches:
            found.append((account, matches))

    if not found:
        typer.echo("No transcripts found matching the query.")
        return

    def preview():
        for account, matches in found:
            typer.echo(f"Found {len(matches)} transcript(s) for profile '{account.profile}':")
            for m in matches:
                typer.echo(f"  [{m.date}] {m.subject or 'Untitled'} (doc_id={m.doc_id})")

    def fetch():
        transcripts = []
        for account, matches in found:
            transcripts.extend(fetch_transcripts(profile=account.profile, matches=matches))
        return transcripts

    run(
        fetch=fetch,
        config=config,
        dry_run=dry_run,
        enrich_transcripts=enrich,
        clean=clean,
        preview=preview,
    )


@app.command()
def slack(
    channel: Annotated[str | None, typer.Option(help="Slack channel ID")] = None,
    days: Annotated[int | None, typer.Option(help="How many days back to search")] = None,
    date_from: Annotated[str | None, typer.Option("--from", help="Start date (YYYY-MM-DD)")] = None,
    date_to: Annotated[str | None, typer.Option("--to", help="End date (YYYY-MM-DD)")] = None,
    enrich: Annotated[bool, typer.Option("--enrich", help="Run LLM enrichment (summary, topics, participants)")] = False,
    clean: Annotated[bool, typer.Option("--clean", help="Also generate a cleaned version of the transcript (implies --enrich)")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    config = load_config()
    resolved_channel = channel or config.slack.channel
    parsed_from, parsed_to = _resolve_dates(date_from, date_to)
    resolved_days = days or config.lookback_days

    if not resolved_channel:
        typer.echo("Error: No Slack channel configured. Set sources.slack.channel in .transcripts/config.yaml or use --channel.", err=True)
        raise typer.Exit(code=1)

    label = _date_label(date_from, date_to, resolved_days)
    typer.echo(f"Searching Slack files in channel '{resolved_channel}' ({label})...")

    try:
        matches = slack_list(
            channel=resolved_channel,
            lookback_days=resolved_days,
            date_from=parsed_from,
            date_to=parsed_to,
        )
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    if not matches:
        typer.echo("No transcripts found.")
        return

    def preview():
        typer.echo(f"Found {len(matches)} transcript(s):")
        for m in matches:
            typer.echo(f"  [{m.date}] {m.title or 'Untitled'} (file_id={m.file_id})")

    run(
        fetch=lambda: slack_fetch(matches),
        config=config,
        dry_run=dry_run,
        enrich_transcripts=enrich,
        clean=clean,
        preview=preview,
    )


@app.command()
def clipboard(
    title: Annotated[str | None, typer.Option(help="Title for the transcript")] = None,
    enrich: Annotated[bool, typer.Option("--enrich", help="Run LLM enrichment (summary, topics, participants)")] = False,
    clean: Annotated[bool, typer.Option("--clean", help="Also generate a cleaned version of the transcript (implies --enrich)")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    try:
        text = subprocess.run(["pbpaste"], capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        typer.echo("Error: pbpaste not found. Clipboard source is only supported on macOS.", err=True)
        raise typer.Exit(code=1)

    if not text.strip():
        typer.echo("Clipboard is empty.")
        return

    typer.echo(f"Read {len(text)} characters from clipboard.")

    raw = RawTranscript(
        text=text,
        source="clipboard",
        date=date.today(),
        source_id=hashlib.sha256(text.encode()).hexdigest()[:16],
        title=title,
    )

    config = load_config()
    run(
        fetch=lambda: [raw],
        config=config,
        dry_run=dry_run,
        enrich_transcripts=enrich,
        clean=clean,
        preview=lambda: typer.echo(f"  [preview] First 200 chars: {text[:200]}..."),
    )


@app.command()
def file(
    path: Annotated[str, typer.Argument(help="Path to transcript file")],
    title: Annotated[str | None, typer.Option(help="Title for the transcript")] = None,
    enrich: Annotated[bool, typer.Option("--enrich", help="Run LLM enrichment (summary, topics, participants)")] = False,
    clean: Annotated[bool, typer.Option("--clean", help="Also generate a cleaned version of the transcript (implies --enrich)")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    from pathlib import Path

    file_path = Path(path)
    if not file_path.exists():
        typer.echo(f"Error: File not found: {path}", err=True)
        raise typer.Exit(code=1)

    text = file_path.read_text(encoding="utf-8")
    if not text.strip():
        typer.echo("File is empty.")
        return

    typer.echo(f"Read {len(text)} characters from {file_path}")

    raw = RawTranscript(
        text=text,
        source="file",
        date=date.today(),
        source_id=hashlib.sha256(text.encode()).hexdigest()[:16],
        title=title or file_path.stem,
    )

    config = load_config()
    run(
        fetch=lambda: [raw],
        config=config,
        dry_run=dry_run,
        enrich_transcripts=enrich,
        clean=clean,
        preview=lambda: typer.echo(f"  [preview] First 200 chars: {text[:200]}..."),
    )
