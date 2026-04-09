# Story 1: Gmail Transcript Ingestion

## User Story

As an engineer, I want to ingest a meeting transcript from my Gmail account, so that I can process it through the transcript pipeline.

## Value

Delivers the primary input mechanism — authenticates with Gmail, queries for transcript emails, resolves linked Google Docs, and extracts plain text content ready for processing.

## Scope

Full-stack: CLI command (`transcript ingest gmail`) + Gmail OAuth flow + Google Drive API extraction + credential storage.

## Size

Medium (5-8 days)

## Acceptance Criteria

### AC1: Query Gmail for transcript emails
- **Given** valid stored credentials
- **When** `transcript ingest gmail` is run
- **Then** Gmail API is queried using the configured query (e.g. `subject:transcript newer_than:1d`)

### AC2: Extract Google Docs link from email
- **Given** a matching email containing a Google Docs link
- **When** the email is processed
- **Then** the Google Doc ID is correctly resolved from the link

### AC3: Fetch document content via Drive API
- **Given** a valid Google Doc ID
- **When** fetched via the Drive API
- **Then** the document is exported as plain text and returned for processing

### AC4: Trigger OAuth flow when no credentials exist
- **Given** no stored credentials for the active profile
- **When** the command is run
- **Then** the OAuth flow is triggered (scopes: `gmail.readonly`, `drive.readonly`)
- **And** on success, credentials are stored at `~/.config/transcript/credentials/<profile>.json`

### AC5: Reuse stored credentials
- **Given** valid credentials already exist for the active profile
- **When** the command is run again
- **Then** stored credentials are reused without re-authenticating

### AC6: Handle no matching emails
- **Given** valid credentials
- **When** the Gmail query returns no results
- **Then** a clear message is displayed (e.g. "No transcript emails found matching query")

### AC7: Support --profile flag
- **Given** a `--profile <name>` flag is provided
- **When** authenticating or reading credentials
- **Then** credentials are stored/read per profile name

## Technical Notes

- Gmail API scopes: `gmail.readonly`, `drive.readonly`
- Credential storage path: `~/.config/transcript/credentials/<profile>.json`
- Default query configurable via `.transcripts/config.yaml` under `sources.gmail.query`
- Google Doc export format: plain text (`text/plain`)

## Dependencies

None — this is a starting story.

## References

- [Transcript CLI Architecture Guide](../transcript_cli_architecture_and_implementation_guide.md) — Sections 4, 6, 7
