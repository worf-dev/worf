import click
from worf.settings import settings
from .models import Organization
import logging

logger = logging.getLogger(__name__)


@click.group("organizations")
def organizations():
    """
    Organizations-related functionality.
    """
    pass


@organizations.command("list")
def list():
    """
    List all organizations with name and ID.
    """
    with settings.session() as session:
        organizations = session.query(Organization).all()
        click.echo("{:<30s}\t{:<32s}".format("Name", "ID"))
        click.echo("-" * 30 + "\t" + "-" * 32)
        for organization in organizations:
            click.echo(f"{organization.name:<30s}\t{organization.ext_id.hex:<32s}")
