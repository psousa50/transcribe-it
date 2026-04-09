# Story 2: Transcript Normalisation

## User Story

As an engineer, I want raw transcript text to be normalised before enrichment, so that the LLM receives clean, consistent input.

## Value

Ensures the processing pipeline has a reliable intermediate step that removes noise while preserving structure and meaning, regardless of input source.

## Scope

Normalisation pipeline step — takes raw text in, returns cleaned text out. No LLM involvement.

## Size

Small (1-3 days)

## Acceptance Criteria

### AC1: Remove obvious noise
- **Given** raw transcript text containing noise (e.g. "[inaudible]", repeated timestamps, join/leave notifications)
- **When** the text is normalised
- **Then** obvious noise is removed

### AC2: Preserve structure and meaning
- **Given** raw transcript text with speaker labels, paragraphs, and dialogue structure
- **When** the text is normalised
- **Then** the original structure and meaning are preserved

### AC3: Pass through clean text unchanged
- **Given** transcript text that is already clean
- **When** the text is normalised
- **Then** it passes through unchanged

### AC4: Consistent output format across sources
- **Given** transcript text from different sources (Gmail extraction, clipboard, file)
- **When** each is normalised
- **Then** the output format is consistent

## Technical Notes

- This is intentionally minimal per the spec — "Remove obvious noise, preserve original structure, no heavy parsing"
- Should be a pure function: text in, text out
- No LLM calls — deterministic processing only

## Dependencies

None — can be developed in parallel with all other stories.

## References

- [Transcript CLI Architecture Guide](../transcript_cli_architecture_and_implementation_guide.md) — Section 8
