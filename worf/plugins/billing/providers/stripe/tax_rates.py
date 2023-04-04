from .base import StripeService


class TaxRates(StripeService):
    def update_or_create(self, tax_rate_provider):
        if tax_rate_provider.provider_id is not None:
            response = self.get(f"/v1/tax_rates/{tax_rate_provider.provider_id}")
            if response.status_code == 200:
                # this tax_rate already exists, we update it
                return self.update(tax_rate_provider)
        # this tax_rate does not exist yet
        return self.create(tax_rate_provider)

    def update(self, tax_rate_provider):
        tax_rate = tax_rate_provider.tax_rate
        request_data = {
            "display_name": tax_rate.name,
            "active": tax_rate.active,
            "description": tax_rate.description,
            "jurisdiction": tax_rate.jurisdiction,
        }
        response = self.post(
            f"/v1/tax_rates/{tax_rate_provider.provider_id}", data=request_data
        )
        response.raise_for_status()
        data = response.json()
        tax_rate_provider.provider_data = data
        return data

    def create(self, tax_rate_provider):
        """
        Create a tax_rate and update the resulting data.
        """
        tax_rate = tax_rate_provider.tax_rate
        request_data = {
            "inclusive": tax_rate.inclusive,
            "percentage": tax_rate.percentage,
            "display_name": tax_rate.name,
            "active": tax_rate.active,
            "description": tax_rate.description,
            "jurisdiction": tax_rate.jurisdiction,
        }
        response = self.post("/v1/tax_rates", data=request_data)
        response.raise_for_status()
        data = response.json()
        tax_rate_provider.provider_id = data["id"]
        tax_rate_provider.provider_data = data
        return data
