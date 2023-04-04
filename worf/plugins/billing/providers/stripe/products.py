from .base import StripeService


class Products(StripeService):
    def update_or_create(self, product_provider):
        if product_provider.provider_id is not None:
            response = self.get(f"/v1/products/{product_provider.provider_id}")
            if response.status_code == 200:
                # this product already exists, we update it
                return self.update(product_provider)
        # this product does not exist yet
        return self.create(product_provider)

    def update(self, product_provider):
        response = self.post(
            f"/v1/products/{product_provider.provider_id}",
            data={
                "name": product_provider.product.name,
                "active": product_provider.product.active,
            },
        )
        response.raise_for_status()
        data = response.json()
        product_provider.provider_data = data
        return data

    def create(self, product_provider):
        """
        Create a product and update the resulting data.
        """
        response = self.post(
            "/v1/products",
            data={
                "id": product_provider.provider_id,
                "name": product_provider.product.name,
                "type": product_provider.product.type,
                "active": product_provider.product.active,
            },
        )
        response.raise_for_status()
        data = response.json()
        product_provider.provider_id = data["id"]
        product_provider.provider_data = data
        return data
