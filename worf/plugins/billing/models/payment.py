from worf.models.base import Base, PkType
from sqlalchemy import Column, DateTime, Boolean, Unicode, ForeignKey, Integer
from sqlalchemy_utils import JSONType
from sqlalchemy.orm import relationship, backref


class Payment(Base):

    """
    Describes a payment, which is always linked to a given invoice.
    """

    __tablename__ = "payment"

    def export(self):
        return {"id": str(self.ext_id)}

    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)

    # datetime when the payment was made
    paid_at = Column(DateTime, nullable=False)

    # payment amount can be negative in case of a refund
    amount = Column(Integer, nullable=False)
    currency = Column(Unicode, nullable=False)

    invoice_id = Column(PkType, ForeignKey("invoice.id"), nullable=False)
    invoice = relationship(
        "Invoice", backref=backref("payments", cascade="all,delete,delete-orphan")
    )

    payment_method_id = Column(PkType, ForeignKey("payment_method.id"), nullable=False)
    payment_method = relationship(
        "PaymentMethod", backref=backref("payments", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get_or_create(cls, session, invoice):
        payment = (
            session.query(Payment)
            .filter(Payment.invoice_id == invoice.id)
            .one_or_none()
        )
        if not payment:
            payment = Payment(invoice=invoice, provider=invoice.provider)
            session.add(payment)
        return payment
