import subprocess
import click
import re
import os
import tempfile

from worf.settings import settings


@click.group("worker")
def worker():
    """
    Worker-related functionality.
    """
    pass


@worker.command("run")
def run_worker():
    """
    Run the worker.
    """
    settings.worker.run()
