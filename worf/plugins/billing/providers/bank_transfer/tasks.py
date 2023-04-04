from worf.settings import settings
import logging

logger = logging.getLogger(__name__)


@settings.register_task
def generate_invoices():
    pass


def process_event(event):
    pass
