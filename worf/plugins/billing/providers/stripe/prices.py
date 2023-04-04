from .base import StripeService


class Prices(StripeService):
    def update_or_create(self, price_provider):
        product_provider = price_provider.price.product.provider("stripe")
        if product_provider is None:
            raise ValueError("product provider not found")
        api_prices = []
        while True:
            response = self.get(
                f"/v1/prices",
                params={
                    "product": product_provider.provider_id,
                    "limit": 100,
                    "starting_after": api_prices[-1]["id"] if api_prices else None,
                },
            )
            data = response.json()
            response.raise_for_status()
            api_prices.extend(data["data"])
            if not data["has_more"]:
                break
        for price_obj in api_prices:
            if price_obj["nickname"] == price_provider.price.name:
                price_provider.provider_id = price_obj["id"]
                price_provider.provider_data = price_obj
                return self.update(price_provider)
        # this price does not exist yet
        return self.create(price_provider)

    def update(self, price_provider):
        response = self.post(
            f"/v1/prices/{price_provider.provider_id}",
            data={
                "nickname": price_provider.price.name,
                "active": price_provider.price.active,
            },
        )
        response.raise_for_status()
        data = response.json()
        for k in ("unit_amount", "currency"):
            if data[k] != getattr(price_provider.price, k):
                raise ValueError(f"price information does not match for key {k}")
        price_provider.provider_data = data
        return data

    def create(self, price_provider):
        """
        Create a price  and update the resulting data.
        """
        product_provider = price_provider.price.product.provider("stripe")
        if product_provider is None:
            raise ValueError("product provider not found")
        request_data = {
            "nickname": price_provider.price.name,
            "unit_amount": price_provider.price.unit_amount,
            "currency": price_provider.price.currency,
            "active": price_provider.price.active,
            "product": product_provider.provider_id,
        }
        if price_provider.price.type == "recurring":
            request_data.update(
                {
                    "recurring[interval]": price_provider.price.billing_interval,
                    "recurring[usage_type]": price_provider.price.usage_type,
                }
            )

        response = self.post("/v1/prices", data=request_data)
        response.raise_for_status()
        data = response.json()
        price_provider.provider_id = data["id"]
        price_provider.provider = "stripe"
        price_provider.provider_data = data
        return data

    def list(self):
        pass
