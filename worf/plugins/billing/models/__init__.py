from .event import Event
from .customer import Customer, CustomerProvider
from .payment_method import PaymentMethod
from .invoice import Invoice, InvoiceItem
from .subscription import (
    Subscription,
    SubscriptionProvider,
    SubscriptionItem,
    SubscriptionItemProvider,
)
from .payment import Payment
from .price import Price, PriceProvider
from .product import Product, ProductProvider
from .tax_rate import TaxRate, TaxRateProvider


def clean_db(session):
    for model in [
        Payment,
        PaymentMethod,
        InvoiceItem,
        Invoice,
        SubscriptionItemProvider,
        SubscriptionItem,
        SubscriptionProvider,
        Subscription,
        Event,
        CustomerProvider,
        Customer,
        PriceProvider,
        Price,
        ProductProvider,
        Product,
        TaxRateProvider,
        TaxRate,
    ]:
        session.query(model).delete()
