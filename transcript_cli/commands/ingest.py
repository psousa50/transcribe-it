import hashlib
import subprocess
from datetime import date
from typing import Annotated

import typer

from transcript_cli.config import load_config
from transcript_cli.models import RawTranscript
from transcript_cli.pipeline.run import run
from transcript_cli.sources.gmail import build_query, fetch_transcripts, list_emails
from transcript_cli.sources.slack import fetch_transcripts as slack_fetch, list_files as slack_list

app = typer.Typer(name="ingest", no_args_is_help=True)


def _resolve_dates(date_from, date_to):
    parsed_from = date.fromisoformat(date_from) if date_from else None
    parsed_to = date.fromisoformat(date_to) if date_to else None
    return parsed_from, parsed_to


def _date_label(date_from, date_to, days):
    if date_from or date_to:
        return f"{date_from or '...'} to {date_to or '...'}"
    return f"last {days} day(s)"


@app.command()
def gmail(
    profile: Annotated[str | None, typer.Option(help="Gmail auth profile")] = None,
    days: Annotated[int | None, typer.Option(help="How many days back to search")] = None,
    date_from: Annotated[str | None, typer.Option("--from", help="Start date (YYYY-MM-DD)")] = None,
    date_to: Annotated[str | None, typer.Option("--to", help="End date (YYYY-MM-DD)")] = None,
    subject: Annotated[str | None, typer.Option(help="Filter by email subject")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    config = load_config()
    resolved_profile = profile or config.gmail.profile
    parsed_from, parsed_to = _resolve_dates(date_from, date_to)
    resolved_days = days or config.lookback_days

    if not config.gmail.sender:
        typer.echo("Error: No Gmail sender configured. Set sources.gmail.sender in .transcripts/config.yaml.", err=True)
        raise typer.Exit(code=1)

    resolved_query = build_query(config.gmail.sender, resolved_days, date_from=parsed_from, date_to=parsed_to, subject=subject)
    label = _date_label(date_from, date_to, resolved_days)
    typer.echo(f"Searching emails with profile '{resolved_profile}' ({label})...")

    try:
        matches = list_emails(profile=resolved_profile, query=resolved_query, subject_filter=subject)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    if not matches:
        typer.echo("No transcripts found matching the query.")
        return

    def preview():
        typer.echo(f"Found {len(matches)} transcript(s):")
        for m in matches:
            typer.echo(f"  [{m.date}] {m.subject or 'Untitled'} (doc_id={m.doc_id})")

    run(
        fetch=lambda: fetch_transcripts(profile=resolved_profile, matches=matches),
        config=config,
        dry_run=dry_run,
        preview=preview,
    )


@app.command()
def slack(
    channel: Annotated[str | None, typer.Option(help="Slack channel ID")] = None,
    days: Annotated[int | None, typer.Option(help="How many days back to search")] = None,
    date_from: Annotated[str | None, typer.Option("--from", help="Start date (YYYY-MM-DD)")] = None,
    date_to: Annotated[str | None, typer.Option("--to", help="End date (YYYY-MM-DD)")] = None,
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
        preview=preview,
    )


@app.command()
def clipboard(
    title: Annotated[str | None, typer.Option(help="Title for the transcript")] = None,
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
        preview=lambda: typer.echo(f"  [preview] First 200 chars: {text[:200]}..."),
    )


@app.command()
def file(
    path: Annotated[str, typer.Argument(help="Path to transcript file")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    typer.echo("Not yet implemented")
