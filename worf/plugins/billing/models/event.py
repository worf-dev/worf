from worf.models.base import Base, PkType
from sqlalchemy import Column, Unicode, DateTime
from sqlalchemy_utils import JSONType

from sqlalchemy.orm import relationship, backref


class Event(Base):

    """
    Describes an event.
    """

    __tablename__ = "billing_event"

    def export(self):
        return {"id": str(self.ext_id)}

    # the provider that handles this customer, e.g. Stripe
    provider_data = Column(JSONType, index=False, nullable=True)
    # the ID of this object at the provider (if it exists)
    provider_id = Column(Unicode, nullable=True)
    # the name of the provider
    provider = Column(Unicode, nullable=False)
    # the type of the event
    type = Column(Unicode, nullable=False)
    # the status of the event
    status = Column(Unicode, nullable=False, default="unprocessed")
    # the timestamp of the event
    timestamp = Column(DateTime)
