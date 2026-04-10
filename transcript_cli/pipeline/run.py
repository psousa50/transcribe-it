from collections.abc import Callable
from pathlib import Path

import typer

from transcript_cli.config import TranscriptConfig
from transcript_cli.models import RawTranscript
from transcript_cli.pipeline.enrich import enrich
from transcript_cli.storage.local import DuplicateTranscriptError, persist


def run(
    fetch: Callable[[], list[RawTranscript]],
    config: TranscriptConfig,
    dry_run: bool = False,
    preview: Callable[[], None] | None = None,
) -> None:
    if preview:
        preview()

    if dry_run:
        return

    typer.echo("Fetching and processing...")
    transcripts = fetch()

    if not transcripts:
        typer.echo("No transcripts to process.")
        return

    for raw in transcripts:
        typer.echo(f"  [{raw.date}] {raw.title or 'Untitled'}")

        enriched = enrich(raw, raw.text)

        base_path = Path(config.local.path)
        try:
            output_dir = persist(enriched, base_path)
            typer.echo(f"    Saved to {output_dir}")
        except DuplicateTranscriptError:
            typer.echo("    Skipped — already ingested")
