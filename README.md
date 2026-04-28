# transcribe-it

A lightweight CLI for ingesting meeting transcripts (Gmail or Slack), enriching them with an LLM, and storing the results as local files.

```
Source -> Extract -> LLM Enrich -> Local Files
```

## Prerequisites

- Python 3.12+
- A Google Cloud project with Gmail API + Google Drive API enabled (for the Gmail source), or a Slack bot token (for the Slack source)
- An API key for one of the supported LLM providers (Anthropic, OpenAI, or Groq) — only needed if you want LLM enrichment

## Install

```bash
uv tool install transcribe-it
```

Or with pipx:

```bash
pipx install transcribe-it
```

## Setup

Run the interactive setup from the directory where you want transcripts to be stored:

```bash
transcribe-it init
```

This will:

- Ask which sources to enable (Gmail, Slack)
- Prompt for the credentials each source needs
- Optionally let you pick an LLM provider and store the API key (skip this if you only want raw transcripts)
- Write `.transcripts/config.yaml` in the current directory
- Write secrets to `~/.config/transcript/env`

### Gmail credentials

For Gmail you'll be asked for `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`. Two options:

1. **Reuse someone else's OAuth client** — ask a teammate for the values and have them add your Google account as a Test user on their OAuth consent screen.
2. **Create your own** — in Google Cloud Console, create an OAuth 2.0 Client ID of type *Desktop app*, then copy the client ID and secret from the resulting credentials.

After `init`, authenticate:

```bash
transcribe-it auth gmail
```

### Slack credentials

For Slack you'll be asked for the channel ID and a bot token (`xoxb-...`). The bot needs to be a member of the channels you want to ingest from.

## Usage

By default, ingestion only extracts the raw transcript — no LLM call, no API key required. Pass `--enrich` to also generate a summary, topics, and participants via LLM.

```bash
# Last N days, raw extraction only (default)
transcribe-it ingest gmail --days 7

# With LLM enrichment
transcribe-it ingest gmail --days 7 --enrich

# Enrichment + cleaned transcript variant (--clean implies --enrich)
transcribe-it ingest gmail --days 7 --clean

# Specific date range
transcribe-it ingest gmail --from 2026-04-01 --to 2026-04-05

# Preview matching emails without fetching or writing
transcribe-it ingest gmail --days 1 --dry-run

# Ingest a single transcript file directly
transcribe-it ingest file path/to/transcript.txt
```

### Output

Raw mode (default) writes a single `.txt` file per transcript:

```
.transcripts/
  2026-04-09-ai-labs-daily.txt
```

With `--enrich`, each transcript becomes a folder:

```
.transcripts/
  2026-04-09-ai-labs-daily/
    raw.txt          # Original transcript (immutable)
    metadata.json    # Source, date, participants, topics, summary
```

With `--clean`, an additional `clean.md` is written (structured: title, summary, topics, cleaned transcript).

### Prompts

LLM prompts are bundled with the package under `transcribe_it/prompts/`. To customise, fork the repo and edit `prompts/enrich.md`.

## Commands

| Command | Description |
|---------|-------------|
| `transcribe-it init` | Interactive setup for sources, credentials, and LLM |
| `transcribe-it auth gmail` | Authenticate with Gmail (OAuth) |
| `transcribe-it ingest gmail` | Ingest transcripts from Gmail |
| `transcribe-it ingest file PATH` | Ingest a single transcript file |

### Ingest options (Gmail)

| Flag | Description |
|------|-------------|
| `--days N` | How many days back to search |
| `--from YYYY-MM-DD` | Start date |
| `--to YYYY-MM-DD` | End date |
| `--profile NAME` | Gmail auth profile |
| `--dry-run` | List matching emails without processing |
| `--enrich` | Run LLM enrichment (summary, topics, participants) |
| `--clean` | Also generate a cleaned version of the transcript (implies `--enrich`) |

## Configuration files

| Path | Purpose |
|------|---------|
| `.transcripts/config.yaml` | Per-project: sources, lookback, output destinations |
| `~/.config/transcript/env` | Global: API keys and OAuth credentials |
