from .base import BankTransferService
from worf.settings import settings
from worf.plugins.billing.models import PaymentMethod


class Checkouts(BankTransferService):
    def create(self, customer_provider, subscription_provider=None, metadata=None):
        with settings.session() as session:
            payment_method = PaymentMethod.get_or_create(
                session, "bank_transfer", customer_provider.customer
            )

            payment_method.live_mode = True
            payment_method.provider = "bank_transfer"

            # we attach the payment method to the subscription (if one is given)
            if subscription_provider is not None:
                session.add(subscription_provider)
                subscription_provider.default_payment_method = payment_method

        return (
            {
                # backend data
            },
            {
                "message": "success",
                # client data
            },
        )
