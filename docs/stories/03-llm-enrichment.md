# Story 3: LLM Enrichment

## User Story

As an engineer, I want normalised transcripts to be enriched by an LLM, so that I get a clean transcript, summary, and extracted topics ready for storage.

## Value

Transforms a normalised transcript into structured, AI-friendly output — the core value-add of the pipeline.

## Scope

LLM prompt construction + API call + response parsing into structured output (clean transcript, summary, topics).

## Size

Medium (3-5 days)

## Acceptance Criteria

### AC1: Produce clean transcript
- **Given** normalised transcript text
- **When** enriched via LLM
- **Then** a cleaned version of the transcript is produced

### AC2: Generate summary
- **Given** normalised transcript text
- **When** enriched via LLM
- **Then** a concise summary of the meeting is generated

### AC3: Extract topics
- **Given** normalised transcript text
- **When** enriched via LLM
- **Then** a list of discussed topics is extracted

### AC4: Do not add information
- **Given** the LLM enrichment prompt
- **When** the LLM processes a transcript
- **Then** no information beyond the original content is added
- **And** original meaning is preserved

### AC5: Support --dry-run
- **Given** the `--dry-run` flag is set
- **When** enrichment completes
- **Then** the result is displayed to stdout but not passed to the persistence step

### AC6: Handle LLM failure gracefully
- **Given** an LLM API call fails (timeout, rate limit, error)
- **When** enrichment is attempted
- **Then** a clear error message is reported
- **And** the pipeline does not write partial output

## Technical Notes

- Prompt constraints: do NOT add information, preserve meaning, remove only clear noise
- Output structure must match what Story 4 (Local File Output) expects for `clean.md` and `metadata.json`
- Consider making the LLM provider configurable (future extensibility, not in scope now)

## Dependencies

- Benefits from Story 2 (Normalisation) output format being settled, but can be developed in parallel against an agreed interface

## References

- [Transcript CLI Architecture Guide](../transcript_cli_architecture_and_implementation_guide.md) — Section 9
