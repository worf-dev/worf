from .base import StripeService


class PaymentMethods(StripeService):
    def get_payment_method(self, id):
        response = self.get(f"/v1/payment_methods/{id}")
        response.raise_for_status()
        return response.json()

    def attach_to_customer(self, payment_method, customer_provider):
        response = self.post(
            f"/v1/payment_methods/{payment_method.provider_id}/attach",
            data={"customer": customer_provider.provider_id},
        )
        response.raise_for_status()
        return response.json()
