import base64
import fnmatch
import os
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from transcribe_it.models import RawTranscript

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

CREDENTIALS_DIR = Path.home() / ".config" / "transcript" / "credentials"


def _build_oauth_client_config() -> dict:
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET must be set. "
            "Run 'transcript init' to configure."
        )
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }

GOOGLE_DOCS_URL_PATTERN = re.compile(
    r"https://docs\.google\.com/document/d/([a-zA-Z0-9_-]+)"
)


def get_credentials(profile: str) -> Credentials:
    token_path = CREDENTIALS_DIR / f"{profile}.json"

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            return creds

    flow = InstalledAppFlow.from_client_config(_build_oauth_client_config(), SCOPES)
    creds = flow.run_local_server(port=0)

    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())

    return creds


def _extract_doc_ids(payload: dict) -> list[str]:
    doc_ids: list[str] = []

    body_data = payload.get("body", {}).get("data", "")
    if body_data:
        decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
        doc_ids.extend(GOOGLE_DOCS_URL_PATTERN.findall(decoded))

    for part in payload.get("parts", []):
        doc_ids.extend(_extract_doc_ids(part))

    return doc_ids


def _get_email_date(headers: list[dict]) -> date:
    for header in headers:
        if header["name"].lower() == "date":
            raw_date = header["value"]
            for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%d %b %Y %H:%M:%S %z"):
                try:
                    return datetime.strptime(raw_date.strip(), fmt).date()
                except ValueError:
                    continue
            break
    return date.today()


def _get_email_subject(headers: list[dict]) -> str | None:
    for header in headers:
        if header["name"].lower() == "subject":
            return header["value"]
    return None


def _fetch_doc_text(drive_service, doc_id: str) -> str:
    return (
        drive_service.files()
        .export(fileId=doc_id, mimeType="text/plain")
        .execute()
        .decode("utf-8")
    )


def _is_glob(pattern: str) -> bool:
    return any(ch in pattern for ch in "*?")


def subject_matches(subject: str | None, patterns: list[str]) -> bool:
    if not patterns:
        return True
    if not subject:
        return False
    lowered = subject.lower()
    return any(
        fnmatch.fnmatch(lowered, p.lower()) if _is_glob(p) else p.lower() in lowered
        for p in patterns
    )


def _subject_clause(patterns: list[str]) -> str | None:
    if not patterns or any(_is_glob(p) for p in patterns):
        return None
    terms = " OR ".join(f'"{p}"' for p in patterns)
    return f"subject:({terms})"


def build_query(
    sender: str,
    lookback_days: int,
    date_from: date | None = None,
    date_to: date | None = None,
    subjects: list[str] | None = None,
) -> str:
    import calendar
    from datetime import timedelta

    today = date.today()
    start = date_from or (today - timedelta(days=lookback_days - 1))
    end = date_to or today
    after_epoch = calendar.timegm(start.timetuple())
    before_epoch = calendar.timegm((end + timedelta(days=1)).timetuple())
    parts = []
    if sender:
        parts.append(f"from:{sender}")
    clause = _subject_clause(subjects or [])
    if clause:
        parts.append(clause)
    parts.append(f"after:{after_epoch}")
    parts.append(f"before:{before_epoch}")
    return " ".join(parts)


@dataclass
class EmailMatch:
    date: date
    subject: str | None
    doc_id: str


def list_emails(
    profile: str, query: str, subject_filters: list[str] | None = None
) -> list[EmailMatch]:
    creds = get_credentials(profile)
    gmail_service = build("gmail", "v1", credentials=creds)

    results = gmail_service.users().messages().list(userId="me", q=query).execute()

    messages = results.get("messages", [])
    if not messages:
        return []

    matches: list[EmailMatch] = []
    seen_doc_ids: set[str] = set()

    for msg_ref in messages:
        message = (
            gmail_service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="full")
            .execute()
        )

        headers = message.get("payload", {}).get("headers", [])
        email_date = _get_email_date(headers)
        subject = _get_email_subject(headers)

        if not subject_matches(subject, subject_filters or []):
            continue

        doc_ids = _extract_doc_ids(message.get("payload", {}))

        for doc_id in doc_ids:
            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)
            matches.append(EmailMatch(date=email_date, subject=subject, doc_id=doc_id))

    return matches


def fetch_transcripts(profile: str, matches: list[EmailMatch]) -> list[RawTranscript]:
    creds = get_credentials(profile)
    drive_service = build("drive", "v3", credentials=creds)

    transcripts: list[RawTranscript] = []
    for match in matches:
        text = _fetch_doc_text(drive_service, match.doc_id)
        transcripts.append(
            RawTranscript(
                text=text,
                source="gmail",
                date=match.date,
                source_id=match.doc_id,
                title=match.subject,
            )
        )

    return transcripts
