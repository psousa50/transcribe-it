import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from transcript_cli.models import RawTranscript


@dataclass
class SlackFileMatch:
    date: date
    title: str | None
    file_id: str
    url_private: str


def _get_client() -> WebClient:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN not set. Add it to your .env file.")
    return WebClient(token=token)


def list_files(
    channel: str,
    lookback_days: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[SlackFileMatch]:
    client = _get_client()
    today = date.today()
    start = date_from or (today - timedelta(days=lookback_days - 1))
    end = date_to or today

    ts_from = int(datetime.combine(start, datetime.min.time()).timestamp())
    ts_to = int(datetime.combine(end + timedelta(days=1), datetime.min.time()).timestamp())

    try:
        response = client.files_list(
            channel=channel,
            ts_from=str(ts_from),
            ts_to=str(ts_to),
            types="text",
        )
    except SlackApiError as e:
        raise RuntimeError(f"Slack API error: {e.response['error']}")

    matches: list[SlackFileMatch] = []
    seen_ids: set[str] = set()

    for f in response.get("files", []):
        file_id = f["id"]
        if file_id in seen_ids:
            continue
        seen_ids.add(file_id)

        file_date = datetime.fromtimestamp(f["created"]).date()
        matches.append(
            SlackFileMatch(
                date=file_date,
                title=f.get("title"),
                file_id=file_id,
                url_private=f["url_private"],
            )
        )

    return matches


def fetch_transcripts(matches: list[SlackFileMatch]) -> list[RawTranscript]:
    client = _get_client()
    transcripts: list[RawTranscript] = []

    for match in matches:
        response = client.api_call(
            api_method="files.info",
            params={"file": match.file_id},
        )
        file_info = response["file"]
        url = file_info.get("url_private_download") or file_info.get("url_private")

        content_response = client.api_call(
            api_method="",
            http_verb="GET",
            api_url=url,
        )
        text = content_response.data.decode("utf-8") if isinstance(content_response.data, bytes) else str(content_response.data)

        transcripts.append(
            RawTranscript(
                text=text,
                source="slack",
                date=match.date,
                source_id=match.file_id,
                title=match.title,
            )
        )

    return transcripts
