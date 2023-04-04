from worf.models import EMailRequest
from worf.plugins.billing.models import Event
from worf.settings import settings
from worf.utils.email import jinja_email, send_email
from worf.utils.pdf import pdf
from sqlalchemy.sql import asc
from .helpers import get_provider
from .providers import providers
import traceback
import logging

logger = logging.getLogger(__name__)


@settings.register_task
def run_maintenance_tasks():
    """
    Runs maintenance tasks (e.g. invoice generation) for all registered providers.
    This is e.g. used by the bank transfer provider to generate and send invoices for
    active subscriptions.
    """
    for provider_name in providers:
        provider = get_provider(provider_name)
        if provider:
            provider.run_maintenance_tasks()


@settings.register_task
def process_events(event_id=None, all=False, type=None, since=None):
    providers = {}
    with settings.session() as session:
        if not all:
            extra_filters = [~Event.status.in_(["processed", "failed"])]
        else:
            extra_filters = []
        if event_id is not None:
            extra_filters = [Event.ext_id == event_id]
        if type:
            extra_filters.append(Event.type == type)
        if since:
            extra_filters.append(Event.timestamp > since)
        events = (
            session.query(Event)
            .filter(*extra_filters)
            .order_by(asc(Event.timestamp))
            .all()
        )
        for event in events:
            logger.info(
                f"Processing event '{event.ext_id.hex}' of type '{event.type}' and timestamp {event.timestamp} (provider: {event.provider}, status: {event.status})"
            )
            pn = event.provider
            if not pn in providers:
                providers[pn] = get_provider(pn)
            providers[pn].process_event(event)


def send_invoice_by_email(session, invoice, email=None):
    """
    We send a copy of the invoice to the customers' e-mail address.
    """
    if email is None:
        email = invoice.customer_email

    if not EMailRequest.request(session, "invoice-copy", email):
        logger.info("Cannot send another e-mail...")
        return
    message = jinja_email("email/invoice.multipart", {"invoice": invoice}, version="v1")
    attachments = {}
    if invoice.pdf is not None:
        logger.info("Attaching invoice PDF...")
        attachments[f"{invoice.number}.pdf"] = invoice.pdf
    invoice.sent_by_email = True
    try:
        send_email(
            to=email,
            subject=message.subject,
            text=message.text,
            html=message.html,
            attachments=attachments,
        )
        invoice_copy_email = settings.get("billing.invoice_copy_email")
        # we send a copy of the e-mail to an internal account (for bookkeeping)
        if invoice_copy_email:
            send_email(
                to=invoice_copy_email,
                subject=message.subject,
                text=message.text,
                html=message.html,
                attachments=attachments,
            )
    except:
        # we fail softly here as we still want to save the invoice and a failing
        # e-mail delivery does not invalidate the other things we did...
        logger.error("Could not send invoice e-mail!")
        logger.error(traceback.format_exc())


def generate_invoice_pdf(invoice):
    """
    We generate a PDF invoice for the customer.
    """
    result = pdf("billing/invoice/invoice.html", {"invoice": invoice})
    invoice.pdf = result
    if settings.get("debug"):
        # if debugging is enabled we store the resulting PDF invoice
        with open(f"/tmp/worf-invoice-{invoice.number}.pdf", "wb") as output_file:
            output_file.write(result)
