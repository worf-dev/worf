from worf.plugins.organizations.models import Organization, OrganizationRole
from worf.settings import settings as settings


def organization(test, fixtures, name):
    organization = Organization(name=name, active=True)
    test.session.add(organization)
    test.session.commit()
    return organization


def organization_role(test, fixtures, user, organization, role):
    role = OrganizationRole(user=user, organization=organization, role=role)
    test.session.add(role)
    test.session.commit()
    return role
