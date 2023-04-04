from .stripe import Stripe
from .bank_transfer import BankTransfer

providers = {"stripe": Stripe, "bank_transfer": BankTransfer}
