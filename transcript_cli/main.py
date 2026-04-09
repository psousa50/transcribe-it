from dotenv import load_dotenv
import typer

load_dotenv()

from transcript_cli.commands.auth import app as auth_app
from transcript_cli.commands.ingest import app as ingest_app

app = typer.Typer(name="transcript", no_args_is_help=True)
app.add_typer(auth_app, name="auth")
app.add_typer(ingest_app, name="ingest")

if __name__ == "__main__":
    app()
