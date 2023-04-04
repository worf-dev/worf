from worf.models.base import Base, PkType
from sqlalchemy import Column, Boolean, Unicode, ForeignKey, Integer
from sqlalchemy_utils import JSONType
from sqlalchemy.orm import relationship, backref


class Product(Base):

    """
    Describes a product.
    """

    __tablename__ = "product"

    def export(self, with_prices=True, access_code=None, for_superuser=False):
        data = {
            "id": str(self.ext_id),
            "name": self.name,
            "active": self.active,
            "type": self.type,
        }
        if with_prices:
            data["prices"] = [
                price.export(for_superuser=for_superuser, access_code=access_code)
                for price in self.prices
                if (not price.testing or for_superuser)
                and (
                    not price.restricted
                    or (access_code is not None and access_code in price.access_codes)
                )
            ]
        return data

    # name of the product
    name = Column(Unicode, nullable=False)
    # whether the product is still active
    active = Column(Boolean, default=True)
    # the type (either 'good' or 'service')
    type = Column(Unicode, nullable=False)

    @classmethod
    def get(cls, session, name):
        return session.query(Product).filter(Product.name == name).one_or_none()

    @classmethod
    def get_or_create(cls, session, name):
        product = cls.get(session, name)
        if not product:
            product = Product(name=name)
            session.add(product)
        return product

    def provider(self, provider):
        pd = [pd for pd in self.providers if pd.provider == provider and pd.active]
        if not pd:
            return None
        return pd[0]


class ProductProvider(Base):

    """
    Maps a product to additional data about it managed by a provider.
    """

    __tablename__ = "product_provider"

    # the provider that handles this invoice, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)
    # whether the invoice provider is active
    active = Column(Boolean, nullable=False, default=True)

    product_id = Column(PkType, ForeignKey("product.id"), nullable=False)
    product = relationship(
        "Product", backref=backref("providers", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get(cls, session, product, provider):
        if product.id is None:
            return
        return (
            session.query(ProductProvider)
            .filter(
                ProductProvider.product == product, ProductProvider.provider == provider
            )
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, product, provider):
        product_provider = cls.get(session, product, provider)
        if not product_provider:
            product_provider = ProductProvider(product=product, provider=provider)
            session.add(product_provider)
        return product_provider
