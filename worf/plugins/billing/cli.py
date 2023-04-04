import click
from worf.settings import settings
from worf.plugins.organizations.models import Organization
from .models import (
    Customer,
    Invoice,
    Product,
    Price,
    Subscription,
    SubscriptionProvider,
    SubscriptionItem,
    TaxRate,
    CustomerProvider,
    SubscriptionItemProvider,
)
from .tasks import (
    send_invoice_by_email,
    generate_invoice_pdf,
    process_events,
    run_maintenance_tasks,
)
from .helpers import get_provider
from .providers import providers
import datetime
import logging

logger = logging.getLogger(__name__)


@click.group("billing")
@click.option("--provider", default=None)
@click.pass_context
def billing(ctx, provider):
    """
    Billing-related functionality.
    """
    ctx.ensure_object(dict)
    if provider is not None and not provider in providers:
        click.echo(f"Unknown provider '{provider}'")
        exit(-1)
    ctx.obj["provider"] = provider


@billing.command("sync")
@click.pass_context
def sync(ctx):
    """
    Synchronize prizes and produces with the provider.
    """
    provider = get_provider(ctx.obj["provider"])
    provider.sync()


@billing.group("events")
def events():
    """
    Event-related functionality.
    """


@events.command("process-all")
@click.option("--all", is_flag=True, default=False)
@click.option("--type", default=None)
@click.option("--since", default=None)
def _process_events(all, type, since):
    """
    Process specified events (see options)
    """
    if since is not None:
        since = datetime.datetime.strptime(since, "%Y-%m-%dT%H:%M:%SZ").astimezone(
            datetime.timezone.utc
        )
    process_events(all=all, type=type, since=since)


@billing.command("run-maintenance")
def _run_maintenance_tasks():
    """
    Run maintenance tasks.
    """
    run_maintenance_tasks()


@events.command("process")
@click.argument("event-id")
def process_event(event_id):
    """
    Process a specific event
    """
    process_events(event_id)


@billing.group("invoices")
def invoices():
    """
    Invoice-related functionality.
    """


@invoices.command("send-email")
@click.pass_context
@click.argument("invoice-id")
@click.option("--email", default=None)
def send_invoice_by_email_command(ctx, invoice_id, email):
    """
    Send an invoice by e-mail to the customer.
    """
    with settings.session() as session:
        invoice = session.query(Invoice).filter(Invoice.id == invoice_id).one_or_none()
        if not invoice:
            click.echo("Invoice not found.")
            return
        send_invoice_by_email(session, invoice, email=email)


@invoices.command("generate-pdf")
@click.pass_context
@click.option("--invoice-id", default=None)
@click.option("--since", default=None)
@click.option("--output", default=None)
def generate_invoice_pdf_command(ctx, invoice_id, since, output):
    """
    Generates the PDF for the given invoice.
    """
    if since is not None:
        since = datetime.datetime.strptime(since, "%Y-%m-%dT%H:%M:%SZ").astimezone(
            datetime.timezone.utc
        )
    with settings.session() as session:
        filters = []
        if invoice_id:
            filters.append(Invoice.id == invoice_id)
        if since:
            filters.append(Invoice.date >= since)
        invoices = session.query(Invoice).filter(*filters).all()
        for invoice in invoices:
            click.echo(f"Generating invoice {invoice.number} PDF...")
            generate_invoice_pdf(invoice)
            if output:
                with open(
                    f"{output}/{invoice.date}-{invoice.number}.pdf", "wb"
                ) as output_file:
                    output_file.write(invoice.pdf)


@invoices.command("list")
def list_invoices():
    """
    List all existing invoices.
    """
    with settings.session() as session:
        invoices = session.query(Invoice).order_by(Invoice.created_at).all()
        click.echo("{:<10s}\t{:<10s}\t{:<32s}".format("ID", "Amount", "Customer"))
        click.echo("-" * 10 + "\t" + "-" * 10 + "\t" + "-" * 32)
        for invoice in invoices:
            click.echo(
                f"{invoice.id:<10d}\t{invoice.amount:<10d}\t{invoice.customer_name:<32s}"
            )


@billing.group("customers")
def customers():
    """
    Customer-related functionality.
    """


@customers.command("list")
def list_customers():
    """
    List all existing customers.
    """
    with settings.session() as session:
        customers = session.query(Customer).all()
        click.echo("{:<32s}\t{:<32s}".format("ID", "Organization"))
        click.echo("-" * 32 + "\t" + "-" * 32)
        for customer in customers:
            click.echo(f"{customer.ext_id.hex:<32s}\t{customer.organization.name:<32s}")


@customers.command("create")
@click.argument("organization-name")
@click.pass_context
def create_customer(ctx, organization_name):
    """
    Creates a customer for the given organization (identified by name).
    """
    provider = get_provider(ctx.obj["provider"])
    with settings.session() as session:
        organization = (
            session.query(Organization)
            .filter(Organization.name == organization_name)
            .one_or_none()
        )
        if organization is None:
            click.echo("Organization not found")
            exit(-1)
        customer = Customer.get_or_create(session, organization)
        customer_provider = CustomerProvider.get_or_create(
            session, customer, provider.name
        )
        data = provider.customers.update_or_create(customer_provider)
        click.echo(data)


@billing.group("subscriptions")
def subscriptions():
    """
    Subscriptions-related functionality.
    """


@subscriptions.command("list")
def list_subscriptions():
    """
    List all existing subscriptions.
    """
    with settings.session() as session:
        subscriptions = session.query(Subscription).all()
        click.echo("{:<32s}\t{:<32s}".format("ID", "Organization"))
        click.echo("-" * 32 + "\t" + "-" * 32)
        for subscription in subscriptions:
            click.echo(
                f"{subscription.ext_id.hex:<32s}\t{subscription.customer.organization.name:<32s}"
            )


@customers.command("create-checkout-session")
@click.argument("customer-id")
@click.pass_context
def checkout_session(ctx, customer_id):
    """
    Generate a checkout session for the given customer. A checkout session
    creates a payment method and associates it with the customer.
    """
    provider = get_provider(ctx.obj["provider"])
    if not hasattr(provider, "checkouts"):
        click.echo("Provider does not support checkouts")
        exit(-1)
    with settings.session() as session:
        customer = (
            session.query(Customer).filter(Customer.ext_id == customer_id).one_or_none()
        )
        if customer is None:
            click.echo("Customer not found")
            exit(-1)
        customer_provider = customer.provider(provider.name)
        if customer_provider is None:
            click.echo("Customer provider not found")
            exit(-1)
        data, client_data = provider.checkouts.create(customer_provider)
        click.echo(data, client_data)


@customers.command("subscribe")
@click.argument("organization-name")
@click.argument("product-name")
@click.argument("price-name")
@click.pass_context
def subscribe_customer(ctx, organization_name, product_name, price_name):
    """
    Subscribe a customer to a given price of a given product.
    """
    provider = get_provider(ctx.obj["provider"])
    with settings.session() as session:
        organization = (
            session.query(Organization)
            .filter(Organization.name == organization_name)
            .one_or_none()
        )
        if organization is None:
            click.echo("Organization not found")
            exit(-1)
        customer = Customer.get(session, organization)
        if customer is None:
            click.echo("Customer not found")
            exit(-1)
        product = Product.get(session, product_name)
        if product is None:
            click.echo("Product not found")
            exit(-1)
        price = Price.get(session, product, price_name)
        if price is None:
            click.echo("Price not found")
            exit(-1)
        click.echo(
            f"Subscribing organization '{organization.name}' to product '{product.name}'' with price '{price.name}''"
        )
        # create a subscription for the given price and customer
        subscription = Subscription(
            customer=customer,
            start_date=datetime.date.today(),
            # trial_end_date=datetime.date.today() + datetime.timedelta(days=7),
        )
        session.add(subscription)
        tax_rates = [tr for tr in session.query(TaxRate).all() if tr.percentage == 0.0]
        if len(tax_rates) == 0:
            click.echo("No valid tax rate found")
            exit(-1)
        tax_rate = tax_rates[0]
        subscription_item = SubscriptionItem(
            subscription=subscription, price=price, tax_rate=tax_rate, quantity=1
        )
        session.add(subscription_item)
        subscription_provider = SubscriptionProvider(
            subscription=subscription, provider=provider.name
        )
        session.add(subscription_provider)
        subscription_item_provider = SubscriptionItemProvider(
            subscription_item=subscription_item, provider=provider.name
        )
        session.add(subscription_item_provider)
        provider.subscriptions.create(subscription_provider)
