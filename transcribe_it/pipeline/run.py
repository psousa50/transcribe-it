from collections.abc import Callable
from pathlib import Path

import typer

from transcribe_it.config import TranscriptConfig
from transcribe_it.models import RawTranscript
from transcribe_it.pipeline.enrich import enrich
from transcribe_it.storage.local import DuplicateTranscriptError, persist, persist_raw


def run(
    fetch: Callable[[], list[RawTranscript]],
    config: TranscriptConfig,
    dry_run: bool = False,
    enrich_transcripts: bool = False,
    clean: bool = False,
    preview: Callable[[], None] | None = None,
) -> None:
    if preview:
        preview()

    if dry_run:
        return

    if clean:
        enrich_transcripts = True

    typer.echo("Fetching and processing...")
    transcripts = fetch()

    if not transcripts:
        typer.echo("No transcripts to process.")
        return

    base_path = Path(config.local.path)

    for raw in transcripts:
        typer.echo(f"  [{raw.date}] {raw.title or 'Untitled'}")

        try:
            if enrich_transcripts:
                enriched = enrich(raw, raw.text, clean=clean)
                output_dir = persist(enriched, base_path, clean=clean)
            else:
                output_dir = persist_raw(raw, base_path)
            typer.echo(f"    Saved to {output_dir}")
        except DuplicateTranscriptError:
            typer.echo("    Skipped — already ingested")
