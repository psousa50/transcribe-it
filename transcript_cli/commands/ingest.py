from datetime import date
from pathlib import Path
from typing import Annotated

import typer

from transcript_cli.config import load_config
from transcript_cli.pipeline.enrich import enrich
from transcript_cli.sources.gmail import build_query, fetch_transcripts, list_emails
from transcript_cli.storage.local import DuplicateTranscriptError, persist

app = typer.Typer(name="ingest", no_args_is_help=True)


def _process_and_persist(raw_transcripts, config):
    for raw in raw_transcripts:
        typer.echo(f"  [{raw.date}] {raw.title or 'Untitled'}")

        enriched = enrich(raw, raw.text)

        base_path = Path(config.local.path)
        try:
            output_dir = persist(enriched, base_path)
            typer.echo(f"    Saved to {output_dir}")
        except DuplicateTranscriptError:
            typer.echo(f"    Skipped — already ingested")


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

    if not config.gmail.sender:
        typer.echo("Error: No Gmail sender configured. Set sources.gmail.sender in .transcripts/config.yaml.", err=True)
        raise typer.Exit(code=1)

    parsed_from = date.fromisoformat(date_from) if date_from else None
    parsed_to = date.fromisoformat(date_to) if date_to else None
    resolved_days = days or config.lookback_days
    resolved_query = build_query(config.gmail.sender, resolved_days, date_from=parsed_from, date_to=parsed_to, subject=subject)

    if parsed_from or parsed_to:
        label = f"{date_from or '...'} to {date_to or '...'}"
    else:
        label = f"last {resolved_days} day(s)"
    typer.echo(f"Searching emails with profile '{resolved_profile}' ({label})...")

    try:
        matches = list_emails(profile=resolved_profile, query=resolved_query, subject_filter=subject)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    if not matches:
        typer.echo("No transcripts found matching the query.")
        return

    typer.echo(f"Found {len(matches)} transcript(s):")
    for m in matches:
        typer.echo(f"  [{m.date}] {m.subject or 'Untitled'} (doc_id={m.doc_id})")

    if dry_run:
        return

    typer.echo("Fetching and processing...")
    transcripts = fetch_transcripts(profile=resolved_profile, matches=matches)
    _process_and_persist(transcripts, config)


@app.command()
def clipboard(
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    typer.echo("Not yet implemented")


@app.command()
def file(
    path: Annotated[str, typer.Argument(help="Path to transcript file")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without writing files")] = False,
) -> None:
    typer.echo("Not yet implemented")
