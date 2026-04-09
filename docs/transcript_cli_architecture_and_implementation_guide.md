# Transcript CLI – Technical Architecture & Implementation Guide

## 1. Overview

This document describes a lightweight, file-based system for ingesting, enriching, and storing meeting transcripts for AI-driven workflows.

The system is intentionally simple:

```
extract → normalize → enrich (LLM) → persist (files)
```

No backend services, databases, or pipelines are required.

---

## 2. Goals

- Make transcripts immediately usable by AI tools
- Avoid infrastructure (no DB, no services)
- Support multiple input sources
- Enable multi-team / multi-repo usage
- Keep system deterministic and debuggable

---

## 3. High-Level Architecture

### Components

1. CLI Tool
2. Source Adapters (Gmail, Slack, Clipboard, File)
3. LLM Enrichment Layer
4. File-Based Storage
5. Optional Destinations (Git, Confluence)

---

## 4. CLI Interface

### Core Commands

```bash
transcript ingest gmail
transcript ingest slack
transcript ingest clipboard
transcript ingest file <path>
```

### Optional Flags

```bash
--context <name>         # e.g. backend, payments
--profile <auth_profile> # gmail/slack auth profile
--dry-run                # no write
```

---

## 5. Configuration

### Project-level config

Location:

```
.transcripts/config.yaml
```

Example:

```yaml
context: backend

sources:
  gmail:
    profile: default
    query: "subject:transcript newer_than:1d"


destinations:
  - type: local
    path: .transcripts/

  - type: git
    repo: git@github.com:company/transcripts.git
    base_path: /
```

---

## 6. Authentication

### Gmail (OAuth)

Command:

```bash
transcript auth gmail --profile default
```

Stored in:

```
~/.config/transcript/credentials/<profile>.json
```

Required scopes:

- gmail.readonly
- drive.readonly

---

## 7. Extraction Layer

### Gmail Flow

1. Query Gmail API
2. Extract Google Docs link
3. Extract document ID
4. Fetch document via Drive API
5. Export as plain text

---

### Clipboard / File

- Read raw text
- No parsing required

---

## 8. Normalization (Minimal)

- Remove obvious noise
- Preserve original structure
- No heavy parsing

---

## 9. LLM Enrichment

### Input

Raw transcript text

### Output

- Clean transcript
- Summary
- Topics

### Prompt Constraints

- Do NOT add information
- Preserve meaning
- Remove only clear noise

---

## 10. Storage Model

### Directory Structure

```
.transcripts/
  <context>/
    <date>-<slug>/
      raw.txt
      clean.md
      metadata.json
```

---

### File Definitions

#### raw.txt

- Original transcript (immutable)

#### clean.md

```md
# Title

## Summary
...

## Topics
- ...

## Transcript
...
```

#### metadata.json

```json
{
  "context": "backend",
  "source": "gmail",
  "date": "2026-04-09",
  "participants": [],
  "topics": []
}
```

---

## 11. Context Model

### Definition

Context = logical grouping (team/domain)

Examples:

- backend
- payments
- product
- cross-team

### Usage

```bash
transcript ingest gmail --context backend
```

---

## 12. Destinations

### 12.1 Local

Write to project repo:

```
.transcripts/
```

---

### 12.2 Git (Shared Repo)

Process:

1. Clone repo (if needed)
2. Write under:

```
<repo>/<context>/<meeting>/
```

3. Commit + push

---

### 12.3 Confluence (Optional)

- Create/update page per meeting
- Upload summary + transcript

---

## 13. Deduplication

Preferred key:

```
Google Doc ID
```

Fallback:

```
hash(start_time + participants + transcript_prefix)
```

---

## 14. Execution Flow

```
CLI
→ extract source
→ fetch transcript
→ normalize
→ LLM enrich
→ write to destinations
```

---

## 15. Example End-to-End

```bash
transcript ingest gmail --context backend
```

Produces:

```
.transcripts/backend/2026-04-09-auth-sync/
```

Then usable by AI tools directly.

---

## 16. Design Principles

- File-first, not DB-first
- AI-friendly structure
- Minimal parsing
- Deterministic pipeline
- Context-driven organization

---

## 17. Future Extensions (Optional)

- Decision extraction
- Action tracking
- Cross-meeting linking
- Search/index layer

---

## 18. Summary

This system provides:

- Immediate usability
- Zero infrastructure
- High compatibility with AI tools
- Scalable organization via context

It is intentionally minimal and can evolve incrementally.

