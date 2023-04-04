from .base import BankTransferService
import datetime


class Subscriptions(BankTransferService):
    def update_or_create(self, subscription_provider):
        if subscription_provider.provider_id:
            return self.update(subscription_provider)
        else:
            return self.create(subscription_provider)

    def cancel(self, subscription_provider):
        subscription = subscription_provider.subscription

        # to do: calculate the end date of the subscription
        subscription.status = "canceled"

    def update(self, subscription_provider):
        """
        Update a subscription.
        """
        pass

    def create(self, subscription_provider):
        """
        Creates a subscription and updates the local object.
        """
        pass
