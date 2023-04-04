from .base import StripeService


class SetupIntents(StripeService):
    def get_setup_intent(self, id):
        response = self.get(f"/v1/setup_intents/{id}")
        response.raise_for_status()
        return response.json()
