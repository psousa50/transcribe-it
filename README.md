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

Setup is split into two steps: a one-off global step for credentials, and a per-project step for what to ingest.

### Step 1: Configure credentials (once per machine)

```bash
transcribe-it setup
```

Pick which credentials to set up — Google OAuth (for Gmail), Slack bot token, and/or LLM provider — and the values are written to `~/.config/transcript/env`. Re-run any time to add or rotate values; existing values are preserved unless you confirm overwrite (or pass `--force`).

### Step 2: Initialise a project (per directory)

From the directory where you want transcripts to land:

```bash
transcribe-it init
```

This asks which sources to enable, source-specific config (sender filter, subject filter, channel ID, etc.), output path, and lookback window. Writes `.transcripts/config.yaml`. No secrets prompts — it'll warn if the credentials a chosen source needs aren't set yet.

### Gmail credentials

`setup` asks for `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`. Two options:

1. **Reuse someone else's OAuth client** — ask a teammate for the values and have them add your Google account as a Test user on their OAuth consent screen.
2. **Create your own** — in Google Cloud Console, create an OAuth 2.0 Client ID of type *Desktop app*, then copy the client ID and secret from the resulting credentials.

After `setup` and `init`, authenticate:

```bash
transcribe-it auth gmail
```

### Slack credentials

`setup` asks for `SLACK_BOT_TOKEN` (`xoxb-...`). The bot needs to be a member of the channels you want to ingest from. The channel ID itself is configured per-project in `init`.

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
transcripts/
  2026-04-09-ai-labs-daily.txt
```

With `--enrich`, each transcript becomes a folder:

```
transcripts/
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
| `transcribe-it setup` | Configure global credentials (OAuth, LLM, Slack token) |
| `transcribe-it init` | Initialise project config (sources, output path, lookback) |
| `transcribe-it auth gmail` | Authenticate with Gmail (OAuth) |
| `transcribe-it ingest gmail` | Ingest transcripts from Gmail |
| `transcribe-it ingest file PATH` | Ingest a single transcript file |

### Ingest options (Gmail)

| Flag | Description |
|------|-------------|
| `--days N` | How many days back to search |
| `--from YYYY-MM-DD` | Start date |
| `--to YYYY-MM-DD` | End date |
| `--subject TEXT` | Only emails whose subject matches TEXT; repeatable, `*`/`?` wildcards (overrides config) |
| `--profile NAME` | Gmail auth profile |
| `--dry-run` | List matching emails without processing |
| `--enrich` | Run LLM enrichment (summary, topics, participants) |
| `--clean` | Also generate a cleaned version of the transcript (implies `--enrich`) |

### Subject filters

By default every email from the configured sender is ingested. To narrow it down, set `subject` under `sources.gmail` — a single string or a list:

```yaml
sources:
  gmail:
    sender: gemini-notes@google.com
    subject:
      - AI Labs
      - Weekly*Review
```

A pattern with no wildcards matches anywhere in the subject, so `AI Labs` matches *"Notes: AI Labs daily"*. A pattern containing `*` or `?` is matched against the whole subject instead, so `Weekly*Review` matches *"Weekly Team Review"* but not *"Notes: Weekly Team Review"* — write `*Weekly*Review*` if you want both. Matching is case-insensitive, and an email is kept if **any** pattern matches.

`--subject` overrides the config for one run and can be repeated:

```bash
transcribe-it ingest gmail --subject "AI Labs" --subject "Standup*"
```

## Configuration files

| Path | Purpose |
|------|---------|
| `.transcripts/config.yaml` | Per-project: sources, lookback, output destinations |
| `~/.config/transcript/env` | Global: API keys and OAuth credentials |
