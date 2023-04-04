from worf.models.base import Base, PkType
from sqlalchemy import Column, Boolean, Unicode, Float, ForeignKey, Date
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import JSONType


class TaxRate(Base):

    """
    Describes a tax rate.
    """

    __tablename__ = "tax_rate"

    # name of the price
    name = Column(Unicode, nullable=False)
    # whether the price is still active
    active = Column(Boolean, default=True)
    # tax percentage
    percentage = Column(Float, nullable=False)
    # inclusive or exclusive?
    inclusive = Column(Boolean, default=False)
    # jurisdiction
    jurisdiction = Column(Unicode, nullable=True)
    # valid until
    valid_until = Column(Date, nullable=True)
    # valid from
    valid_from = Column(Date, nullable=True)
    # rule
    rule = Column(Unicode, nullable=True)

    @classmethod
    def get_or_create(cls, session, name):
        tax_rate = session.query(TaxRate).filter(TaxRate.name == name).one_or_none()
        if not tax_rate:
            tax_rate = TaxRate(name=name)
            session.add(tax_rate)
        return tax_rate

    def export(self):
        return {
            "id": self.ext_id,
            "jurisdiction": self.jurisdiction,
            "inclusive": self.inclusive,
            "percentage": self.percentage,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "active": self.active,
            "name": self.name,
        }

    def provider(self, provider):
        pd = [pd for pd in self.providers if pd.provider == provider and pd.active]
        if not pd:
            return None
        return pd[0]


class TaxRateProvider(Base):

    """
    Maps a tax rate to additional data about it managed by a provider.
    """

    __tablename__ = "tax_rate_provider"

    # the provider that handles this invoice, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)
    # whether the invoice provider is active
    active = Column(Boolean, nullable=False, default=True)

    tax_rate_id = Column(PkType, ForeignKey("tax_rate.id"), nullable=False)
    tax_rate = relationship(
        "TaxRate", backref=backref("providers", cascade="all,delete,delete-orphan")
    )

    @classmethod
    def get(cls, session, tax_rate, provider):
        if tax_rate.id is None:
            return
        return (
            session.query(TaxRateProvider)
            .filter(
                TaxRateProvider.tax_rate == tax_rate,
                TaxRateProvider.provider == provider,
            )
            .one_or_none()
        )

    @classmethod
    def get_or_create(cls, session, tax_rate, provider):
        tax_rate_provider = cls.get(session, tax_rate, provider)
        if not tax_rate_provider:
            tax_rate_provider = TaxRateProvider(tax_rate=tax_rate, provider=provider)
            session.add(tax_rate_provider)
        return tax_rate_provider
