from .base import StripeService
import datetime


class Subscriptions(StripeService):
    def update_or_create(self, subscription_provider):
        if subscription_provider.provider_id:
            return self.update(subscription_provider)
        else:
            return self.create(subscription_provider)

    def cancel(self, subscription_provider):
        response = self.delete(f"/v1/subscriptions/{subscription_provider.provider_id}")
        response.raise_for_status()
        data = response.json()
        subscription_provider.data = data
        subscription = subscription_provider.subscription

        dt = datetime.datetime.fromtimestamp(data["current_period_end"]).astimezone(
            datetime.timezone.utc
        )

        # we update the subscription object
        subscription.end_date = dt
        subscription.status = "canceled"

        return data

    def update(self, subscription_provider):
        request_data = self._get_update_request_data(subscription_provider)
        response = self.post(
            f"/v1/subscriptions/{subscription_provider.provider_id}", data=request_data
        )
        if response.status_code == 400:
            if response.json()["error"]["code"] == "resource_missing":
                logger.warn(
                    f"Customer with provider ID {subscription_provider.provider_id} does not exist anymore, creating it again"
                )
                return self.create(subscription_provider)
        response.raise_for_status()
        data = response.json()
        subscription_provider.provider_data = data
        return data

    def create(self, subscription_provider):
        """
        Creates a subscription and updates the local object.
        """
        request_data = self._get_create_request_data(subscription_provider)
        response = self.post("/v1/subscriptions", data=request_data)
        response.raise_for_status()
        data = response.json()
        subscription_provider.provider_id = data["id"]
        subscription_provider.provider_data = data
        # we update the subscription status
        subscription_provider.subscription.status = data["status"]
        default_payment_method_id = data.get("default_payment_method")
        if default_payment_method_id:
            default_payment_method = next(
                (
                    pm
                    for pm in subscription_provider.subscription.customer.payment_methods
                    if pm.provider == "stripe"
                    and pm.provider_id == default_payment_method_id
                ),
                None,
            )
            if default_payment_method:
                subscription_provider.default_payment_method = default_payment_method
        return data

    def set_default_payment_method(self, subscription_provider, payment_method):
        if payment_method.provider != "stripe":
            raise ValueError("can only set a stripe payment method")
        if not payment_method.provider_id:
            raise ValueError("payment method has no provider ID")
        request_data = {"default_payment_method": payment_method.provider_id}
        response = self.post(
            f"/v1/subscriptions/{subscription_provider.provider_id}", data=request_data
        )
        response.raise_for_status()
        data = response.json()
        subscription_provider.provider_data = data
        return data

    def _get_update_request_data(self, subscription_provider):
        data = {}
        return data

    def _get_create_request_data(self, subscription_provider):
        subscription = subscription_provider.subscription
        customer_provider = subscription.customer.provider("stripe")
        # if this customer has a payment method on file we try to link it to the
        # subscription instead of asking for a new one again...
        if customer_provider is None:
            raise ValueError("customer provider not found")
        default_payment_method = customer_provider.provider_data.get(
            "invoice_settings", {}
        ).get("default_payment_method")
        data = {
            "customer": customer_provider.provider_id,
            "default_payment_method": default_payment_method,
        }
        if subscription.trial_end_date is not None:
            ed = subscription.trial_end_date
            # we convert the date to a unix timestamp (UTC)
            data["trial_end"] = int(
                datetime.datetime(
                    day=ed.day,
                    month=ed.month,
                    year=ed.year,
                    tzinfo=datetime.timezone.utc,
                ).timestamp()
            )
        for i, item in enumerate(subscription.items):
            price_provider = item.price.provider("stripe")
            if price_provider is None:
                raise ValueError("price provider not found")
            tax_rate_provider = item.tax_rate.provider("stripe")
            if tax_rate_provider is None:
                raise ValueError("tax rate provider not found")
            data[f"items[{i}][price]"] = price_provider.provider_id
            data[f"items[{i}][quantity]"] = item.quantity
            data[f"items[{i}][tax_rates][]"] = f"{tax_rate_provider.provider_id}"
        return data
