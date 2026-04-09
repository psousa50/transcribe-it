from typing import Annotated

import typer

from transcript_cli.sources.gmail import CREDENTIALS_DIR, get_credentials

app = typer.Typer(name="auth", no_args_is_help=True)


@app.command()
def gmail(
    profile: Annotated[str, typer.Option(help="Auth profile name")] = "default",
) -> None:
    token_path = CREDENTIALS_DIR / f"{profile}.json"

    if token_path.exists():
        typer.echo(f"Already authenticated for profile '{profile}'.")
        typer.echo(f"Credentials stored at: {token_path}")
        typer.echo("To re-authenticate, delete the file and run this command again.")
        return

    try:
        get_credentials(profile)
        typer.echo(f"Authenticated successfully for profile '{profile}'.")
        typer.echo(f"Credentials stored at: {token_path}")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
