import requests
from requests.auth import HTTPBasicAuth


class StripeService:
    def __init__(self, config):
        self.config = config

    @property
    def base_url(self):
        return self.config.get("url", "https://api.stripe.com")

    def request(self, method, url, **kwargs):
        return method(
            f"{self.base_url}{url}",
            auth=HTTPBasicAuth(self.config["private_key"], ""),
            **kwargs,
        )

    def get(self, url, **kwargs):
        return self.request(requests.get, url, **kwargs)

    def post(self, url, **kwargs):
        return self.request(requests.post, url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request(requests.patch, url, **kwargs)

    def put(self, url, **kwargs):
        return self.request(requests.put, url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request(requests.delete, url, **kwargs)
