import click

from worf.settings import settings
from worf.models.user import User


@click.group("user")
def user():
    """
    User-related commands.
    """
    pass


@user.command("create")
@click.argument("email")
@click.option("--superuser", is_flag=True)
def create_user(email, superuser):
    """
    Create a user
    """
    with settings.session() as session:
        if User.get_by_email(session, email):
            click.echo("User already exists.")
            return
        user = User(email=email, superuser=superuser)
        session.add(user)


@user.command("update")
@click.argument("email")
@click.option("--superuser", is_flag=True)
def update(email, superuser):
    """
    Update a user
    """
    with settings.session() as session:
        user = User.get_by_email(session, email)
        if not user:
            click.echo("User does not exist.")
            return
        click.echo("Setting superuser to {}".format(superuser))
        user.superuser = superuser
        session.add(user)
