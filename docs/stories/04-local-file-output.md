# Story 4: Local File Output

## User Story

As an engineer, I want processed transcripts to be persisted as local files, so that they are immediately usable by AI tools and searchable in my project.

## Value

Completes the pipeline by writing structured output to the file system in a deterministic, AI-friendly format.

## Scope

File writing + directory structure creation + metadata generation + deduplication.

## Size

Small (2-3 days)

## Acceptance Criteria

### AC1: Create all output files
- **Given** enriched transcript output (clean transcript, summary, topics, raw text)
- **When** persisted
- **Then** three files are created: `raw.txt`, `clean.md`, and `metadata.json`

### AC2: Organise by context
- **Given** a `--context <name>` flag (e.g. `backend`)
- **When** persisted
- **Then** files are written under `.transcripts/<context>/`

### AC3: Name directory by date and slug
- **Given** a transcript date and title
- **When** the output directory is created
- **Then** it is named `<date>-<slug>/` (e.g. `2026-04-09-auth-sync/`)

### AC4: Structure clean.md correctly
- **Given** the `clean.md` file
- **When** opened
- **Then** it contains sections: Title, Summary, Topics, and Transcript (in that order)

### AC5: Structure metadata.json correctly
- **Given** the `metadata.json` file
- **When** read
- **Then** it contains: `context`, `source`, `date`, `participants`, and `topics` fields

### AC6: Deduplicate by Google Doc ID
- **Given** a transcript that has already been ingested (same Google Doc ID)
- **When** ingested again
- **Then** it is not written again
- **And** a message indicates the transcript was already ingested

### AC7: Support --dry-run
- **Given** the `--dry-run` flag is set
- **When** the pipeline completes
- **Then** no files are written to disk

## Technical Notes

- Directory structure: `.transcripts/<context>/<date>-<slug>/`
- Deduplication key: Google Doc ID (preferred), fallback: `hash(start_time + participants + transcript_prefix)`
- `raw.txt` is immutable — original transcript, never modified after creation
- Default context configurable via `.transcripts/config.yaml`

## Dependencies

None — can be developed in parallel with Stories 1-3 against an agreed output interface.

## References

- [Transcript CLI Architecture Guide](../transcript_cli_architecture_and_implementation_guide.md) — Sections 10, 13
