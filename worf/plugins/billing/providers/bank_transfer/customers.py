from .base import BankTransferService

import logging

logger = logging.getLogger(__name__)


class Customers(BankTransferService):
    def update_or_create(self, customer_provider):
        pass

    def update(self, customer_provider):
        pass

    def create(self, customer_provider):
        pass
