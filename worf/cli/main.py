from worf.settings import settings
from worf.cli import commands

import click
import os
import sys
import logging

logger = logging.getLogger(__name__)


@click.group()
@click.option("-v", "--verbose", count=True, default=2)
def worf(verbose):
    settings.setup_logging(verbose)
    if not settings.validate():
        logger.error("Invalid settings encountered:")
        logger.error(settings.form.format_errors())
        sys.exit(-1)

    settings.initialize()


for command in commands:
    worf.add_command(command)


def main():
    for plugin in settings.get("plugins", {}):
        config = settings.load_plugin_config(plugin)
        if "commands" in config:
            for command in config["commands"]:
                worf.add_command(command)
    worf()


if __name__ == "__main__":
    main()
