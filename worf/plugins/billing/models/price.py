from worf.models.base import Base, PkType
from sqlalchemy import Column, Boolean, Unicode, ForeignKey, Integer
from sqlalchemy_utils import JSONType
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects import postgresql


class Price(Base):

    """
    Describes a price.
    """

    __tablename__ = "price"

    def export(self, with_product=False, for_superuser=False, access_code=None):
        data = {
            "id": str(self.ext_id),
            "name": self.name,
            "active": self.active,
            "billing_interval": self.billing_interval,
            "unit_amount": self.unit_amount,
            "currency": self.currency,
            "type": self.type,
            "restricted": self.restricted,
            "usage_type": self.usage_type,
        }
        if access_code and access_code in self.access_codes:
            data["with_access_code"] = True
        if for_superuser:
            data["testing"] = self.testing
        if with_product:
            data["product"] = self.product.export(with_prices=False)
        return data

    # name of the price
    name = Column(Unicode, nullable=False)
    # whether the price is restricted by access codes
    restricted = Column(Boolean, default=False)
    # whether the price is only for testing
    testing = Column(Boolean, default=False)
    # whether the price is still active
    active = Column(Boolean, default=True)
    # billing interval of the product (monthly, yearly)
    billing_interval = Column(Unicode, nullable=False)
    # price of the product as an integer
    unit_amount = Column(Integer, nullable=False)
    # currency that belongs to the price
    currency = Column(Unicode, nullable=False)
    # the type (either one-time or recurring)
    type = Column(Unicode, nullable=False)
    # the usage type (either licensed or metered)
    usage_type = Column(Unicode, nullable=True)

    access_codes = Column(
        postgresql.ARRAY(Unicode, dimensions=1), nullable=False, default=[]
    )

    # the price associated with this price
    product_id = Column(PkType, ForeignKey("product.id"), nullable=False)
    product = relationship(
        "Product", backref=backref("prices", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get(cls, session, product, name):
        return (
            session.query(Price)
            .filter(Price.name == name, Price.product_id == product.id)
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, product, name):
        price = cls.get(session, product, name)
        if not price:
            price = Price(name=name, product=product)
            session.add(price)
        return price

    def provider(self, provider):
        pd = [pd for pd in self.providers if pd.provider == provider and pd.active]
        if not pd:
            return None
        return pd[0]


class PriceProvider(Base):

    """
    Maps a price to additional data about it managed by a provider.
    """

    __tablename__ = "price_provider"

    # the provider that handles this invoice, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)
    # whether the invoice provider is active
    active = Column(Boolean, nullable=False, default=True)

    price_id = Column(PkType, ForeignKey("price.id"), nullable=False)
    price = relationship(
        "Price", backref=backref("providers", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get(cls, session, price, provider):
        if price.id is None:
            return
        return (
            session.query(PriceProvider)
            .filter(PriceProvider.price == price, PriceProvider.provider == provider)
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, price, provider):
        price_provider = cls.get(session, price, provider)
        if not price_provider:
            price_provider = PriceProvider(price=price, provider=provider)
            session.add(price_provider)
        return price_provider
