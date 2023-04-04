from worf.models.base import Base, PkType
from sqlalchemy import (
    Column,
    Unicode,
    UnicodeText,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship, backref


class Organization(Base):

    """
    Describes an organization.
    """

    __tablename__ = "organization"

    def export(self):
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active": self.active,
            "id": str(self.ext_id),
        }

    name = Column(Unicode, nullable=False)
    description = Column(UnicodeText, nullable=True, index=False)
    active = Column(Boolean, nullable=False, default=True)
    users = relationship(
        "User", secondary="organization_role", backref="organizations", viewonly=True
    )
    invitations = relationship(
        "Invitation",
        secondary="organization_invitation",
        backref="organizations",
        viewonly=True,
    )


class OrganizationRole(Base):
    __tablename__ = "organization_role"

    def export(self, org_view=False, with_org=True, with_user=True):
        if org_view:
            e = self.organization.export()
            e["role"] = {
                "name": self.role if isinstance(self.role, str) else self.role.value,
                "confirmed": self.confirmed,
            }
            return e

        d = {"confirmed": self.confirmed, "role": self.role, "id": str(self.ext_id)}

        if with_org:
            d["organization"] = self.organization.export()
        if with_user:
            d["user"] = self.user.export()

        return d

    @classmethod
    def get_or_create(cls, session, organization, user, role):
        org_role = (
            session.query(cls)
            .filter(
                cls.organization == organization, cls.user == user, cls.role == role
            )
            .one_or_none()
        )
        if org_role is None:
            org_role = cls(user=user, organization=organization, role=role)
            session.add(org_role)
        return org_role

    organization_id = Column(PkType, ForeignKey("organization.id"), nullable=False)
    user_id = Column(PkType, ForeignKey("user.id"), nullable=False)

    role = Column(Unicode, nullable=False)

    confirmed = Column(Boolean, default=True)

    organization = relationship(
        "Organization",
        backref=backref("organization_roles", cascade="all,delete,delete-orphan"),
    )
    user = relationship(
        "User",
        backref=backref("organization_roles", cascade="all,delete,delete-orphan"),
    )


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitation"

    def export(self, with_org=True):
        base = self.invitation.export()
        base["invitation_id"] = base["id"]
        base.update(
            {"confirmed": self.confirmed, "role": self.role, "id": str(self.ext_id)}
        )

        if with_org:
            base["organization"] = self.organization.export()
        return base

    organization_id = Column(PkType, ForeignKey("organization.id"), nullable=False)
    invitation_id = Column(PkType, ForeignKey("invitation.id"), nullable=False)
    role = Column(Unicode, nullable=False)

    confirmed = Column(Boolean, default=True)

    organization = relationship(
        "Organization",
        backref=backref("organization_invitations", cascade="all,delete,delete-orphan"),
    )
    invitation = relationship("Invitation")

    @classmethod
    def get_by_invitation_id(cls, session, invitation_id):
        return (
            session.query(cls).filter(cls.invitation_id == invitation_id).one_or_none()
        )

    @classmethod
    def get_by_ext_id(cls, session, ext_id):
        return session.query(cls).filter(cls.ext_id == ext_id).one_or_none()
