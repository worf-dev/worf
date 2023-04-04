from .organization import Organization, OrganizationRole, OrganizationInvitation


def clean_db(session):
    session.query(OrganizationInvitation).delete()
    session.query(OrganizationRole).delete()
    session.query(Organization).delete()
