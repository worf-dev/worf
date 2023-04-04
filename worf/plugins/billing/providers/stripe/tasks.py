from worf.settings import settings
from ...models import (
    CustomerProvider,
    PaymentMethod,
    Event,
    Subscription,
    SubscriptionItem,
    SubscriptionProvider,
    SubscriptionItemProvider,
    Price,
    PriceProvider,
    TaxRate,
    TaxRateProvider,
    Invoice,
    InvoiceItem,
)
from sqlalchemy.orm import joinedload
from .stripe import Stripe
from ...tasks import generate_invoice_pdf, send_invoice_by_email
import traceback
import requests
import datetime

import logging

logger = logging.getLogger(__name__)


def get_processors():
    prefix = "stripe_process_"
    processors = {}
    for function_name in globals():
        if function_name.startswith(prefix):
            processors[function_name[len(prefix) :].replace("_", ".")] = globals()[
                function_name
            ]
    return processors


def process_event(event):
    processors = get_processors()
    with settings.session() as session:
        session.add(event)
        if not event.type in processors:
            return
        processor = processors[event.type]
        try:
            status = processor(session, event)
            if status:
                event.status = "deferred"
            else:
                event.status = "processed"
        except:
            event.status = "failed"
            event.data = {"error": traceback.format_exc()}
            logger.error(traceback.format_exc())


@settings.register_task
def process_hook(data):
    with settings.session() as session:
        dt = datetime.datetime.fromtimestamp(data["created"]).astimezone(
            datetime.timezone.utc
        )
        event = Event(
            provider="stripe",
            provider_id=data["id"],
            provider_data=data,
            status="unprocessed",
            type=data["type"],
            timestamp=dt,
        )
        session.add(event)
    process_event(event)


def stripe_process_customer_subscription_created(session, event):
    return create_or_update_subscription(session, event)


def stripe_process_customer_subscription_updated(session, event):
    return create_or_update_subscription(session, event)


def create_or_update_subscription(session, event):
    provider = Stripe()
    data = event.provider_data
    subscription = data["data"]["object"]
    subscription_provider = (
        session.query(SubscriptionProvider)
        .filter(
            SubscriptionProvider.provider == "stripe",
            SubscriptionProvider.provider_id == subscription["id"],
        )
        .options(
            joinedload(SubscriptionProvider.subscription, innerjoin=True).joinedload(
                Subscription.items
            )
        )
        .one_or_none()
    )
    if not subscription_provider:
        logger.info("No subscription provider found")
        return
    items = subscription["items"]["data"]
    # we deactivate the old subscription items
    for existing_item in subscription_provider.subscription.items:
        existing_item.active = False
    for item in items:
        subscription_item_provider = (
            session.query(SubscriptionItemProvider)
            .filter(
                SubscriptionItemProvider.provider_id == item["id"],
                SubscriptionItemProvider.provider == "stripe",
            )
            .options(
                joinedload(
                    SubscriptionItemProvider.subscription_item, innerjoin=True
                ).joinedload(SubscriptionItem.price, innerjoin=True),
                joinedload(
                    SubscriptionItemProvider.subscription_item, innerjoin=True
                ).joinedload(SubscriptionItem.tax_rate, innerjoin=True),
            )
            .one_or_none()
        )
        if not subscription_item_provider:
            price_provider = (
                session.query(PriceProvider)
                .filter(
                    PriceProvider.provider_id == item["price"]["id"],
                    PriceProvider.provider == "stripe",
                )
                .options(joinedload(PriceProvider.price, innerjoin=True))
                .one_or_none()
            )
            if not price_provider:
                return True
            subscription_item = SubscriptionItem.get_or_create(
                session, subscription_provider.subscription, price_provider.price
            )
            # we make sure the item is active
            subscription_item.active = True
            subscription_item_provider = SubscriptionItemProvider.get_or_create(
                session, subscription_item, "stripe"
            )
            subscription_item_provider.provider_id = item["id"]
            subscription_item_provider.provider_data = item
            if len(item["tax_rates"]) > 0:
                tax_rate = item["tax_rates"][0]
                if len(item["tax_rates"]) > 1:
                    logger.warn("Warning, more than one tax rate detected...")
                tax_rate_provider = (
                    session.query(TaxRateProvider)
                    .filter(
                        TaxRateProvider.provider_id == tax_rate["id"],
                        TaxRateProvider.provider == "stripe",
                    )
                    .options(joinedload(TaxRateProvider.tax_rate, innerjoin=True))
                    .one_or_none()
                )
                if tax_rate_provider:
                    subscription_item.tax_rate = tax_rate_provider.tax_rate
            logger.info("Created a subscription item provider for ID {item['id']}")


def stripe_process_invoice_finalized(session, event):
    """
    Get subscription for invoice
    """
    provider = Stripe()
    data = event.provider_data
    invoice_data = data["data"]["object"]

    invoice = None

    with session.no_autoflush:
        for line in invoice_data["lines"]["data"]:
            """
            Each line item refers to a subscription and a subscription item (hopefully the same).
            We create an invoice item for each and link it to the main invoice.
            """
            subscription_id = line["subscription"]
            subscription_item_id = line["subscription_item"]
            subscription_item_provider = None
            if subscription_item_id:
                subscription_item_provider = (
                    session.query(SubscriptionItemProvider)
                    .filter(
                        SubscriptionItemProvider.provider_id == subscription_item_id,
                        SubscriptionItemProvider.provider == "stripe",
                    )
                    .options(
                        joinedload(
                            SubscriptionItemProvider.subscription_item, innerjoin=True
                        )
                        .joinedload(SubscriptionItem.subscription, innerjoin=True)
                        .joinedload(Subscription.providers)
                    )
                    .one_or_none()
                )
                if not subscription_item_provider:
                    logger.warn(
                        "No subscription provider found, skipping invoice for now..."
                    )
                    # there is no subscription provider for this invoice (yet), so we skip
                    # the processing and try again later.
                    return True
                subscription_provider = (
                    subscription_item_provider.subscription_item.subscription.provider(
                        "stripe"
                    )
                )
                if not subscription_provider:
                    logger.warn(
                        "No subscription provider found, skipping invoice for now..."
                    )
                    # there is no subscription provider for this invoice (yet), so we skip
                    # the processing and try again later.
                    return True

                if invoice is None:
                    invoice = Invoice.get_or_create(
                        session, invoice_data["id"], "stripe"
                    )

                    invoice.provider_data = invoice_data
                    invoice.amount = invoice_data["amount_due"]
                    invoice.date = datetime.date.fromtimestamp(invoice_data["date"])
                    invoice.tax = invoice_data["tax"]
                    invoice.currency = invoice_data["currency"]
                    invoice.period_start = datetime.date.fromtimestamp(
                        invoice_data["period_start"]
                    )
                    invoice.period_end = datetime.date.fromtimestamp(
                        invoice_data["period_end"]
                    )
                    invoice.status = invoice_data["status"]
                    invoice.invoice_reason = invoice_data["billing_reason"]
                    invoice.number = invoice_data["number"]

                if invoice.subscription is None:
                    invoice.subscription = (
                        subscription_item_provider.subscription_item.subscription
                    )

                    customer = invoice.subscription.customer

                    invoice.customer_name = customer.name
                    invoice.customer_additional_name = customer.additional_name
                    invoice.customer_street = customer.street
                    invoice.customer_city = customer.city
                    invoice.customer_zip_code = customer.zip_code
                    invoice.customer_country = customer.country
                    invoice.customer_additional_address = customer.additional_address
                    invoice.customer_vat_id = customer.vat_id
                    invoice.customer_phone = customer.phone
                    invoice.customer_email = customer.email
                    invoice.customer_website = customer.website

                price_provider = (
                    session.query(PriceProvider)
                    .filter(
                        PriceProvider.provider_id == line["price"]["id"],
                        PriceProvider.provider == "stripe",
                    )
                    .options(joinedload(PriceProvider.price, innerjoin=True))
                    .one_or_none()
                )
                if not price_provider:
                    # if no price is found we try to process this again later...
                    return True

                invoice_item = InvoiceItem.get_or_create(
                    session, invoice, line["id"], price_provider.price, "stripe"
                )
                invoice_item.provider_data = line

                tax_rate_provider = (
                    session.query(TaxRateProvider)
                    .filter(
                        TaxRateProvider.provider_id
                        == line["tax_amounts"][0]["tax_rate"]
                    )
                    .options(joinedload(TaxRateProvider.tax_rate, innerjoin=True))
                ).one_or_none()

                if tax_rate_provider is None:
                    raise ValueError("cannot find tax rate provider")

                invoice_item.tax_rate = tax_rate_provider.tax_rate
                invoice_item.amount = line["amount"]
                invoice_item.quantity = line["quantity"]
                invoice_item.currency = line["currency"]
                invoice_item.description = line["description"]
                invoice_item.tax = 0
                invoice_item.discount = 0

                invoice_item.period_start = datetime.date.fromtimestamp(
                    line["period"]["start"]
                )
                invoice_item.period_end = datetime.date.fromtimestamp(
                    line["period"]["end"]
                )
        if invoice is not None and invoice.pdf is None:
            generate_invoice_pdf(invoice)
        if (
            invoice.customer_email is not None
            and not invoice.sent_by_email
            and invoice.amount > 0
        ):
            logger.info(f"Sending a copy of the invoice to {invoice.customer_email}...")
            send_invoice_by_email(session, invoice)


def stripe_process_customer_updated(session, event):
    provider = Stripe()
    data = event.provider_data
    customer = data["data"]["object"]
    customer_provider = (
        session.query(CustomerProvider)
        .filter(
            CustomerProvider.provider_id == customer["id"],
            CustomerProvider.provider == "stripe",
        )
        .one_or_none()
    )
    if customer_provider is None:
        logger.error(f"Stripe customer '{customer['id']}' not found")
        return
    customer_provider.provider_data = customer


def stripe_process_checkout_session_completed(session, event):
    provider = Stripe()
    data = event.provider_data
    customer_id = data["data"]["object"]["customer"]
    setup_intent_id = data["data"]["object"]["setup_intent"]
    setup_intent = provider.setup_intents.get_setup_intent(setup_intent_id)
    payment_method_data = provider.payment_methods.get_payment_method(
        setup_intent["payment_method"]
    )
    customer_provider = (
        session.query(CustomerProvider)
        .filter(
            CustomerProvider.provider_id == customer_id,
            CustomerProvider.provider == "stripe",
        )
        .one_or_none()
    )
    if customer_provider is None:
        logger.error(f"Stripe customer '{customer_id}' not found")
        return
    payment_method = PaymentMethod(
        customer=customer_provider.customer,
        live_mode=data["livemode"],
        type=payment_method_data["type"],
        provider_data=payment_method_data,
        provider_id=payment_method_data["id"],
        provider="stripe",
    )
    session.add(payment_method)
    # we attach the payment method to the stripe customer
    provider.payment_methods.attach_to_customer(payment_method, customer_provider)
    # we set the payment method as the default payment method for the stripe customer
    provider.customers.set_default_payment_method(customer_provider, payment_method)
    subscription_id = data["data"]["object"]["metadata"].get("subscription")
    if subscription_id:
        subscription = (
            session.query(Subscription)
            .filter(Subscription.ext_id == subscription_id)
            .one_or_none()
        )
        if subscription:
            subscription_provider = subscription.provider("stripe")
            if subscription_provider:
                try:
                    # we attach this payment method to the subscription as well
                    provider.subscriptions.set_default_payment_method(
                        subscription_provider, payment_method
                    )
                except requests.HTTPError as e:
                    if e.response.status_code == 404:
                        logger.info("Subscription has been deleted it seems...")
                        return
                subscription_provider.default_payment_method = payment_method
                subscription.status = "active"
    logger.info("Successfully attached a payment method to customer.")
