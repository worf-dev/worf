from .resources import (
    Customer,
    Invoices,
    PaymentMethods,
    Payments,
    Products,
    Subscriptions,
    TaxRates,
    Checkout,
)

from .resources.admin import Sync

routes = [
    {"/admin/sync": (Sync, {"methods": ["POST"]})},
    {"/admin/sync/<provider_name>": (Sync, {"methods": ["POST"]})},
    {
        "/checkout/<organization_id>/<subscription_id>/<provider_name>": (
            Checkout,
            {"methods": ["POST"]},
        )
    },
    {"/customer/<organization_id>": (Customer, {"methods": ["GET", "POST"]})},
    {"/invoices/<organization_id>": (Invoices, {"methods": ["GET", "POST"]})},
    {
        "/payment_methods/<organization_id>": (
            PaymentMethods,
            {"methods": ["GET", "POST"]},
        )
    },
    {"/payments/<organization_id>": (Payments, {"methods": ["GET"]})},
    {"/subscriptions/<organization_id>": (Subscriptions, {"methods": ["GET"]})},
    {
        "/subscriptions/<organization_id>/<price_id>": (
            Subscriptions,
            {"methods": ["POST"]},
        )
    },
    {
        "/subscriptions/<organization_id>/<subscription_id>": (
            Subscriptions,
            {"methods": ["DELETE"]},
        )
    },
    {"/products": (Products, {"methods": ["GET"]})},
    {"/tax_rates": (TaxRates, {"methods": ["GET"]})},
]
