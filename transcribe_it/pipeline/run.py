from collections.abc import Callable
from pathlib import Path

import typer

from transcribe_it.config import TranscriptConfig
from transcribe_it.models import RawTranscript
from transcribe_it.pipeline.enrich import enrich
from transcribe_it.storage.local import DuplicateTranscriptError, persist


def run(
    fetch: Callable[[], list[RawTranscript]],
    config: TranscriptConfig,
    dry_run: bool = False,
    clean: bool = False,
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

        enriched = enrich(raw, raw.text, clean=clean)

        base_path = Path(config.local.path)
        try:
            output_dir = persist(enriched, base_path, clean=clean)
            typer.echo(f"    Saved to {output_dir}")
        except DuplicateTranscriptError:
            typer.echo("    Skipped — already ingested")
