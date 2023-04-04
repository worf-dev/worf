from worf.models.base import Base, PkType
from sqlalchemy import Column, ForeignKey, Unicode, Boolean
from sqlalchemy_utils import JSONType

from sqlalchemy.orm import relationship, backref


class Customer(Base):

    """
    Describes a customer, which is always linked to an organization.
    """

    __tablename__ = "customer"

    # customer details (required for invoicing)
    name = Column(Unicode, nullable=False)
    additional_name = Column(Unicode, nullable=True)
    street = Column(Unicode, nullable=False)
    city = Column(Unicode, nullable=False)
    zip_code = Column(Unicode, nullable=False)
    country = Column(Unicode, nullable=False)
    additional_address = Column(Unicode, nullable=True)
    vat_id = Column(Unicode, nullable=True)
    phone = Column(Unicode, nullable=True)
    email = Column(Unicode, nullable=True)
    website = Column(Unicode, nullable=True)

    def export(self):
        """
        IMPORTANT: do not expose sensitive / internal information here, this
        is user-visible data!
        """
        return {
            "id": self.ext_id,
            "organization": self.organization.export(),
            "name": self.name,
            "additional_name": self.additional_name,
            "street": self.street,
            "city": self.city,
            "zip_code": self.zip_code,
            "country": self.country,
            "additional_address": self.additional_address,
            "vat_id": self.vat_id,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
        }

    organization_id = Column(PkType, ForeignKey("organization.id"), nullable=False)
    organization = relationship(
        "Organization", backref=backref("customers", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get(cls, session, organization):
        return (
            session.query(Customer)
            .filter(Customer.organization_id == organization.id)
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, organization):
        customer = cls.get(session, organization)
        if not customer:
            customer = Customer(organization=organization)
            session.add(customer)
        return customer

    def provider(self, provider):
        pd = [pd for pd in self.providers if pd.provider == provider and pd.active]
        if not pd:
            return None
        return pd[0]


class CustomerProvider(Base):
    __tablename__ = "customer_provider"

    # the provider that handles this customer, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)
    # whether the customer provider is active
    active = Column(Boolean, nullable=False, default=True)

    customer_id = Column(PkType, ForeignKey("customer.id"), nullable=False)
    customer = relationship(
        "Customer", backref=backref("providers", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get(cls, session, customer, provider):
        if customer.id is None:
            return
        return (
            session.query(CustomerProvider)
            .filter(
                CustomerProvider.customer == customer,
                CustomerProvider.provider == provider,
            )
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, customer, provider):
        customer_provider = cls.get(session, customer, provider)
        if not customer_provider:
            customer_provider = CustomerProvider(customer=customer, provider=provider)
            session.add(customer_provider)
        return customer_provider
