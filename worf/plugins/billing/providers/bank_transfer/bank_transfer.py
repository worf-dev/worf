from .customers import Customers
from .subscriptions import Subscriptions
from .checkouts import Checkouts
from .payments import Payments
from ..base import BaseProvider
from worf.settings import settings

import logging

logger = logging.getLogger(__name__)


class BankTransfer(BaseProvider):

    """
    Provides access to all bank transfer services
    """

    def __init__(self):
        self.config = settings.get("bank_transfer")

    @property
    def name(self):
        return "bank_transfer"

    @property
    def routes(self):
        return []

    @property
    def client_settings(self):
        return {"bank_account": self.config.get("bank_account")}

    @property
    def payment_methods(self):
        return PaymentMethods(self.config)

    @property
    def setup_intents(self):
        return SetupIntents(self.config)

    @property
    def checkouts(self):
        return Checkouts(self.config)

    @property
    def prices(self):
        return Prices(self.config)

    @property
    def products(self):
        return Products(self.config)

    @property
    def subscriptions(self):
        return Subscriptions(self.config)

    @property
    def customers(self):
        return Customers(self.config)

    @property
    def payments(self):
        return Payments(self.config)

    @property
    def tax_rates(self):
        return TaxRates(self.config)

    def run_maintenance_tasks(self):
        """
        We go through all subscriptions that have a "bank transfer" provider.
        We retrieve all invoices for the given subscription and check if we
        need to generate another one. If yes, we calculate the current
        billing period and generate a new invoice for the given subscription.
        """
        logger.info("Running maintenance tasks for bank transfer provider...")

    def sync(self):
        """
        There's nothing to sync for this provider
        """

    def process_event(self, event):
        from .tasks import process_event

        process_event(event)

    def sync_subscriptions(self):
        """
        There's nothing to sync here
        """

    def sync_customers(self):
        """
        There's nothing to sync here
        """

    def sync_tax_rates(self):
        """
        There's nothing to sync here
        """

    def sync_products(self):
        """
        There's nothing to sync here
        """
