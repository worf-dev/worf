from worf.models.base import Base, PkType
from sqlalchemy import Column, Date, Boolean, ForeignKey, Unicode, Integer
from sqlalchemy_utils import JSONType
from sqlalchemy.orm import relationship, backref


class Subscription(Base):

    """
    Describes a subscription, which is always linked to a given customer.
    """

    __tablename__ = "subscription"

    # date when the subscription started
    start_date = Column(Date, nullable=True)
    # date until which the subscription ended (if applicable)
    end_date = Column(Date, nullable=True)
    # date until which the subscription trial ended (if applicable)
    trial_end_date = Column(Date, nullable=True)
    # whether this subscription is still valid
    status = Column(Unicode, default="initialized")

    # the customer associated with this subscription
    customer_id = Column(PkType, ForeignKey("customer.id"), nullable=False)
    customer = relationship(
        "Customer", backref=backref("subscriptions", cascade="all,delete,delete-orphan")
    )

    def export(self):
        """
        IMPORTANT: do not expose sensitive / internal information here, this
        is user-visible data!
        """
        return {
            "id": self.ext_id,
            "customer": self.customer.export(),
            "providers": [provider.export() for provider in self.providers],
            "status": self.status,
            "trial_end_date": self.trial_end_date,
            "end_date": self.end_date,
            "start_date": self.start_date,
            "items": [item.export() for item in self.items],
        }

    def provider(self, provider):
        pd = [pd for pd in self.providers if pd.provider == provider and pd.active]
        if not pd:
            return None
        return pd[0]


class SubscriptionItem(Base):

    """
    Describes an item in a subscription.
    """

    __tablename__ = "subscription_item"

    # the quantity of the price
    quantity = Column(Integer, default=1)

    # the price associated with this item
    price_id = Column(PkType, ForeignKey("price.id"), nullable=False)
    price = relationship(
        "Price",
        backref=backref("subscription_items", cascade="all,delete,delete-orphan"),
    )

    # the subscription associated with this item
    subscription_id = Column(PkType, ForeignKey("subscription.id"), nullable=False)
    subscription = relationship(
        "Subscription", backref=backref("items", cascade="all,delete,delete-orphan")
    )

    # the tax rate associated with this item
    tax_rate_id = Column(PkType, ForeignKey("tax_rate.id"), nullable=True)
    tax_rate = relationship(
        "TaxRate",
        backref=backref("subscription_items", cascade="all,delete,delete-orphan"),
    )

    # whether the subscription item is active
    active = Column(Boolean, nullable=False, default=True)

    def export(self):
        """
        IMPORTANT: do not expose sensitive / internal information here, this
        is user-visible data!
        """
        return {
            "tax_rate": self.tax_rate.export() if self.tax_rate else None,
            "price": self.price.export(with_product=True),
            "quantity": self.quantity,
            "id": self.ext_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "data": self.data,
        }

    @classmethod
    def get(cls, session, subscription, price):
        return (
            session.query(SubscriptionItem)
            .filter(
                SubscriptionItem.subscription_id == subscription.id,
                SubscriptionItem.price_id == price.id,
            )
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, subscription, price):
        item = cls.get(session, subscription, price)
        if not item:
            item = SubscriptionItem(subscription=subscription, price=price)
            session.add(item)
        return item


class SubscriptionProvider(Base):

    """
    Maps a subscription to additional data about it managed by a provider.
    """

    __tablename__ = "subscription_provider"

    # the provider that handles this invoice, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)
    # whether the subscription provider is active
    active = Column(Boolean, nullable=False, default=True)

    subscription_id = Column(PkType, ForeignKey("subscription.id"), nullable=False)
    subscription = relationship(
        "Subscription", backref=backref("providers", cascade="all,delete,delete-orphan")
    )

    # the default payment method associated with this subscription
    default_payment_method_id = Column(
        PkType, ForeignKey("payment_method.id", ondelete="SET NULL"), nullable=False
    )
    default_payment_method = relationship(
        "PaymentMethod",
        backref=backref("subscriptions", cascade="all,delete,delete-orphan"),
    )

    def export(self):
        """
        IMPORTANT: do not expose sensitive / internal information here, this
        is user-visible data!
        """
        return {
            "id": self.ext_id,
            "provider": self.provider,
            "active": self.active,
            "default_payment_method": self.default_payment_method.export()
            if self.default_payment_method is not None
            else None,
        }

    @classmethod
    def get(cls, session, subscription, provider):
        if subscription.id is None:
            return
        return (
            session.query(SubscriptionProvider)
            .filter(
                SubscriptionProvider.subscription == subscription,
                SubscriptionProvider.provider == provider,
            )
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, subscription, provider):
        subscription_provider = cls.get(session, subscription, provider)
        if not subscription_provider:
            subscription_provider = SubscriptionProvider(
                subscription=subscription, provider=provider
            )
            session.add(subscription_provider)
        return subscription_provider


class SubscriptionItemProvider(Base):

    """
    Maps a subscription item to additional data about it managed by a provider.
    """

    __tablename__ = "subscription_item_provider"

    # the provider that handles this invoice, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)
    # whether the subscription item provider is active
    active = Column(Boolean, nullable=False, default=True)

    subscription_item_id = Column(
        PkType, ForeignKey("subscription_item.id"), nullable=False
    )
    subscription_item = relationship(
        "SubscriptionItem",
        backref=backref("providers", cascade="all,delete,delete-orphan"),
    )

    @classmethod
    def get(cls, session, subscription_item, provider):
        if subscription_item.id is None:
            return
        return (
            session.query(SubscriptionItemProvider)
            .filter(
                SubscriptionItemProvider.subscription_item == subscription_item,
                SubscriptionItemProvider.provider == provider,
            )
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, subscription_item, provider):
        subscription_item_provider = cls.get(session, subscription_item, provider)
        if not subscription_item_provider:
            subscription_item_provider = SubscriptionItemProvider(
                subscription_item=subscription_item, provider=provider
            )
            session.add(subscription_item_provider)
        return subscription_item_provider
