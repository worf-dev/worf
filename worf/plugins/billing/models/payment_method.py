from worf.models.base import Base, PkType
from sqlalchemy import Column, Boolean, Unicode, ForeignKey
from sqlalchemy_utils import JSONType
from sqlalchemy.orm import relationship, backref


class PaymentMethod(Base):

    """
    Describes a payment method, which is always linked to a given customer.
    """

    __tablename__ = "payment_method"

    def export(self):
        return {
            "id": str(self.ext_id),
            "provider": self.provider,
            "type": self.type,
            "data": self.type_data,
            "customer": self.customer.export(),
        }

    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)

    # type of the payment method
    type = Column(Unicode, nullable=False)
    type_data = Column(JSONType, index=False, nullable=True)
    live_mode = Column(Boolean, nullable=False, default=False)

    customer_id = Column(PkType, ForeignKey("customer.id"), nullable=False)
    customer = relationship(
        "Customer",
        backref=backref("payment_methods", cascade="all,delete,delete-orphan"),
    )

    @classmethod
    def get_or_create(cls, session, type, customer):
        payment_method = (
            session.query(PaymentMethod)
            .filter(
                PaymentMethod.customer_id == customer.id, PaymentMethod.type == type
            )
            .one_or_none()
        )
        if not payment_method:
            payment_method = PaymentMethod(customer=customer, type=type)
            session.add(payment_method)
        return payment_method
