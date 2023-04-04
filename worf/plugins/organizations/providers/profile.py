from ..models import OrganizationRole

from collections import defaultdict


def organization_profile(profile, user, access_token):
    orgs = {}
    org_roles = defaultdict(list)
    for org_role in user.organization_roles:
        if not org_role.confirmed:
            continue  # we only show confirmed organization roles
        if not org_role.organization.id in orgs:
            orgs[org_role.organization.id] = org_role.organization.export()
        org_roles[org_role.organization.id].append(
            org_role.export(with_org=False, with_user=False)
        )
    for org_id, roles in org_roles.items():
        orgs[org_id]["roles"] = roles
    profile["organizations"] = list(orgs.values())
