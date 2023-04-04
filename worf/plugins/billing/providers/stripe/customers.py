from .base import StripeService

import logging

logger = logging.getLogger(__name__)


class Customers(StripeService):
    def update_or_create(self, customer_provider):
        if customer_provider.provider_id is not None:
            response = self.get(f"/v1/customers/{customer_provider.provider_id}")
            if response.status_code == 200:
                # this customer already exists, we update it
                return self.update(customer_provider)
        # this customer does not exist yet
        return self.create(customer_provider)

    def set_default_payment_method(self, customer_provider, payment_method):
        request_data = self._get_request_data(customer_provider)
        response = self.post(
            f"/v1/customers/{customer_provider.provider_id}",
            data={
                "invoice_settings[default_payment_method]": payment_method.provider_id
            },
        )
        response.raise_for_status()
        data = response.json()
        customer_provider.provider_data = data
        return data

    def update(self, customer_provider):
        request_data = self._get_request_data(customer_provider)
        response = self.post(
            f"/v1/customers/{customer_provider.provider_id}", data=request_data
        )
        response.raise_for_status()
        data = response.json()
        customer_provider.provider_id = data["id"]
        customer_provider.provider_data = data
        return data

    def _get_request_data(self, customer_provider):
        return {
            "metadata[organization_id]": customer_provider.customer.organization.ext_id,
            "email": customer_provider.customer.email,
        }

    def create(self, customer_provider):
        """
        Creates a customer and updates the local object.
        """
        request_data = self._get_request_data(customer_provider)
        response = self.post("/v1/customers", data=request_data)
        response.raise_for_status()
        data = response.json()
        customer_provider.provider_id = data["id"]
        customer_provider.provider_data = data
        return data
