from pathlib import Path

from dotenv import load_dotenv

GLOBAL_ENV_PATH = Path.home() / ".config" / "transcript" / "env"
load_dotenv(dotenv_path=GLOBAL_ENV_PATH)

import typer

from transcribe_it.commands.auth import app as auth_app
from transcribe_it.commands.ingest import app as ingest_app
from transcribe_it.commands.init import app as init_app
from transcribe_it.commands.setup import app as setup_app

app = typer.Typer(name="transcript", no_args_is_help=True)
app.add_typer(setup_app, name="setup")
app.add_typer(init_app, name="init")
app.add_typer(auth_app, name="auth")
app.add_typer(ingest_app, name="ingest")

if __name__ == "__main__":
    app()
