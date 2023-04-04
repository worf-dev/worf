from .customers import Customers
from .subscriptions import Subscriptions
from .products import Products
from .prices import Prices
from .checkouts import Checkouts
from .tax_rates import TaxRates
from .setup_intents import SetupIntents
from .payments import Payments
from .payment_methods import PaymentMethods
from ..base import BaseProvider
from ...models import (
    Product,
    ProductProvider,
    Price,
    PriceProvider,
    TaxRate,
    TaxRateProvider,
)

from worf.settings import settings

import logging

logger = logging.getLogger(__name__)


class Stripe(BaseProvider):

    """
    Provides access to all Stripe services
    """

    def __init__(self):
        self.config = settings.get("stripe")

    @property
    def name(self):
        return "stripe"

    @property
    def routes(self):
        from .api.routes import routes

        return routes

    @property
    def client_settings(self):
        return {
            "public_key": self.config.get("public_key"),
            "success_url": self.config.get("success_url"),
            "cancel_url": self.config.get("cancel_url"),
            "payment_types": self.config.get("payment_types"),
        }

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

    def sync(self):
        self.sync_products()
        self.sync_tax_rates()
        self.sync_customers()
        self.sync_subscriptions()

    def process_event(self, event):
        from .tasks import process_event

        process_event(event)

    def sync_subscriptions(self):
        """
        Subscriptions are synced only from Stripe to the local database.
        """
        pass

    def sync_customers(self):
        """
        Customers are synced only from Stripe to the local database.
        """
        pass

    def sync_tax_rates(self):
        """
        Synchronizes tax rates via the Stripe API
        """
        logger.info("Synchronizing tax rates...")
        tax_rate_specs = settings.get("billing.tax_rates")
        tax_rates = []
        for tax_rate_spec in tax_rate_specs:
            with settings.session() as session:
                tax_rate = TaxRate.get_or_create(session, tax_rate_spec["name"])
                for k, v in tax_rate_spec.items():
                    if k.startswith("_"):
                        continue
                    setattr(tax_rate, k, v)
                tax_rate_provider = TaxRateProvider.get_or_create(
                    session, tax_rate, "stripe"
                )
                self.tax_rates.update_or_create(tax_rate_provider)
                tax_rates.append(tax_rate_provider)
        return tax_rates

    def sync_products(self):
        """
        Synchronizes products and prices via the Stripe API
        """
        logger.info("Synchronizing products...")
        product_specs = settings.get("billing.products")
        for product_spec in product_specs:
            with settings.session() as session:
                product = Product.get_or_create(session, product_spec["name"])
                # we update the values of the price
                for k, v in product_spec.items():
                    if k.startswith("_"):
                        continue
                    setattr(product, k, v)
                product_provider = ProductProvider.get_or_create(
                    session, product, "stripe"
                )
                self.products.update_or_create(product_provider)
            for price_spec in product_spec.get("_prices", []):
                with settings.session() as session:
                    price = Price.get_or_create(session, product, price_spec["name"])
                    for k, v in price_spec.items():
                        if k.startswith("_"):
                            continue
                        setattr(price, k, v)
                    price_provider = PriceProvider.get_or_create(
                        session, price, "stripe"
                    )
                    self.prices.update_or_create(price_provider)
