from worf.models.base import Base, PkType
from sqlalchemy import (
    Column,
    DateTime,
    Date,
    Boolean,
    Unicode,
    ForeignKey,
    LargeBinary,
    Integer,
)

from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import JSONType


class Invoice(Base):

    """
    Describes an invoice, which is always linked to a subscription.
    """

    __tablename__ = "invoice"

    def export(self):
        return {"id": str(self.ext_id)}

    # the provider that handles this invoice, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)

    date = Column(Date, nullable=False)
    paid_at = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount = Column(Integer, nullable=False)
    tax = Column(Integer, nullable=False)
    currency = Column(Unicode, nullable=False)
    discount = Column(Integer, nullable=False, default=0)
    status = Column(Unicode, nullable=False, default=False)
    invoice_reason = Column(Unicode, nullable=True)
    number = Column(Unicode, nullable=False)
    description = Column(Unicode, nullable=True)
    sent_by_email = Column(Boolean, nullable=False, default=False)

    pdf = Column(LargeBinary, nullable=True)

    # customer details as printed on the invoice
    # we copy these from the customer object to make sure they do not change
    # and are permanently associated with this invoice (compliance)
    customer_name = Column(Unicode, nullable=False)
    customer_additional_name = Column(Unicode, nullable=True)
    customer_street = Column(Unicode, nullable=False)
    customer_city = Column(Unicode, nullable=False)
    customer_zip_code = Column(Unicode, nullable=False)
    customer_country = Column(Unicode, nullable=False)
    customer_additional_address = Column(Unicode, nullable=True)
    customer_vat_id = Column(Unicode, nullable=True)
    customer_phone = Column(Unicode, nullable=True)
    customer_email = Column(Unicode, nullable=True)
    customer_website = Column(Unicode, nullable=True)

    # an invoice is always linked to a subscription
    subscription_id = Column(
        PkType, ForeignKey("subscription.id", ondelete="SET NULL"), nullable=True
    )
    subscription = relationship(
        "Subscription", backref=backref("invoices", cascade="all,delete,delete-orphan")
    )

    # invoices can be linked to other invoices (e.g. when we process a refund)
    linked_invoice_id = Column(
        PkType, ForeignKey("invoice.id", ondelete="SET NULL"), nullable=True
    )
    linked_invoice = relationship(
        "Invoice",
        remote_side="Invoice.id",
        backref=backref("linked_invoices", cascade="all,delete,delete-orphan"),
    )

    @property
    def subtotal(self):
        subtotal = 0
        for item in self.items:
            subtotal += item.amount
        return subtotal

    @classmethod
    def get_or_create(cls, session, id, provider):
        invoice = (
            session.query(Invoice)
            .filter(Invoice.provider_id == id, Invoice.provider == provider)
            .one_or_none()
        )
        if not invoice:
            invoice = Invoice(provider=provider, provider_id=id)
            session.add(invoice)
        return invoice


class InvoiceItem(Base):

    """
    Describes an item in an invoice.
    """

    __tablename__ = "invoice_item"

    # the provider that handles this subscription, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)

    amount = Column(Integer, nullable=False)
    tax = Column(Integer, nullable=False)
    currency = Column(Unicode, nullable=False)
    discount = Column(Integer, nullable=False, default=0)
    description = Column(Unicode, nullable=True)

    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # the quantity of the price
    quantity = Column(Integer, default=1)

    # the price associated with this item
    price_id = Column(PkType, ForeignKey("price.id"), nullable=False)
    price = relationship(
        "Price", backref=backref("invoice_items", cascade="all,delete,delete-orphan")
    )

    # the invoice associated with this item
    invoice_id = Column(PkType, ForeignKey("invoice.id"), nullable=False)
    invoice = relationship(
        "Invoice", backref=backref("items", cascade="all,delete,delete-orphan")
    )

    # the tax rate associated with this item
    tax_rate_id = Column(PkType, ForeignKey("tax_rate.id"), nullable=True)
    tax_rate = relationship(
        "TaxRate", backref=backref("invoice_items", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get_or_create(cls, session, invoice, provider_id, price, provider):
        item = (
            session.query(InvoiceItem)
            .filter(
                InvoiceItem.invoice_id == invoice.id,
                InvoiceItem.provider_id == provider_id,
                InvoiceItem.price_id == price.id,
                InvoiceItem.provider == provider,
            )
            .one_or_none()
        )
        if not item:
            item = InvoiceItem(
                invoice=invoice, price=price, provider_id=provider_id, provider=provider
            )
            session.add(item)
        return item
