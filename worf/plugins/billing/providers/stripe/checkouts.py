from .base import StripeService
from worf.settings import settings


class Checkouts(StripeService):
    def _get_request_data(self, customer_provider, metadata):
        frontend_url = settings.get("frontend.url")
        frontend_paths = settings.get("frontend.paths")
        payment_types = ",".join(self.config.get("payment_types", []))
        config = settings.get("stripe")
        data = {
            "cancel_url": config["cancel_url"],
            "success_url": config["success_url"],
            "mode": "setup",
            "payment_method_types[]": f"{payment_types}",
            "customer": customer_provider.provider_id,
        }
        if metadata is not None:
            for k, v in metadata.items():
                data[f"metadata[{k}]"] = v
        return data

    def create(self, customer_provider, subscription_provider=None, metadata=None):
        """
        Creates a checkout session for the given customer. A checkout
        session does not have a local equivalent as it is specific to Stripe.
        """
        request_data = self._get_request_data(customer_provider, metadata)
        response = self.post("/v1/checkout/sessions", data=request_data)
        response.raise_for_status()
        data = response.json()
        return (
            data,
            {
                "session_id": data["id"],
                "success_url": data["success_url"],
                "cancel_url": data["cancel_url"],
            },
        )
