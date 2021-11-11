import typer
import os
from loader.users import Users

import config

app = typer.Typer()

users_db = Users(
    users_file_path=os.path.join(config.config_path, 'users.json'),
    salt=config.SALT
)


@app.command()
def add(username: str = None, password: str = None, group: str = None):
    users_db.add(username, password, group)


@app.command()
def verify(username: str = None, password: str = None):
    if users_db.verify(username, password):
        typer.echo(f"The user and password are valid !")
    else:
        typer.echo(f"The user and password are not valid !")


@app.command()
def update(username: str = None, password: str = None, group: str = None):
    users_db.update(username, password, group)


@app.command()
def delete(username: str = None):
    users_db.delete(username)


if __name__ == "__main__":
    app()
