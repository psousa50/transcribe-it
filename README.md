# Transcript CLI

A lightweight CLI for ingesting meeting transcripts from Gmail, enriching them with an LLM, and storing the results as local files.

```
Gmail -> Extract Google Doc -> LLM Enrich -> Local Files
```

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Google Cloud project with Gmail API and Google Drive API enabled
- An Anthropic API key (for LLM enrichment)

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure Google OAuth

Create an OAuth 2.0 Client ID (Desktop app) in your Google Cloud Console, download the JSON, and place it at:

```
~/.config/transcript/client_secret.json
```

### 3. Set your API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-key-here
```

### 4. Configure the project

Edit `.transcripts/config.yaml`:

```yaml
sources:
  gmail:
    profile: default
    sender: gemini-notes@google.com

lookback_days: 7

destinations:
  - type: local
    path: .transcripts/
```

### 5. Authenticate with Gmail

```bash
uv run transcribe-it auth gmail
```

## Usage

### Ingest transcripts

```bash
# Last 7 days (default)
make ingest

# Today only
make ingest ARGS="--days 1"

# Specific date range
make ingest ARGS="--from 2026-04-01 --to 2026-04-05"

# Preview what will be ingested (no fetching, no LLM, no writing)
make ingest ARGS="--days 1 --dry-run"
```

Or without Make:

```bash
uv run transcribe-it ingest gmail --days 1
```

### Output

Each transcript produces three files under `.transcripts/`:

```
.transcripts/
  2026-04-09-ai-labs-daily/
    raw.txt          # Original transcript (immutable)
    clean.md         # Structured: title, summary, topics, clean transcript
    metadata.json    # Source, date, participants, topics
```

### Prompts

LLM prompts live in `prompts/` as markdown files. Edit `prompts/enrich.md` to change how transcripts are processed.

## Commands

| Command | Description |
|---------|-------------|
| `transcribe-it auth gmail` | Authenticate with Gmail (OAuth) |
| `transcribe-it ingest gmail` | Ingest transcripts from Gmail |

### Ingest options

| Flag | Description |
|------|-------------|
| `--days N` | How many days back to search |
| `--from YYYY-MM-DD` | Start date |
| `--to YYYY-MM-DD` | End date |
| `--profile NAME` | Gmail auth profile |
| `--dry-run` | List matching emails without processing |
