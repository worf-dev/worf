from .resources.organization import Organizations, OrganizationRoles
from .resources.admin import OrganizationsAdmin, OrganizationRolesAdmin
from .resources.invitations import OrganizationInvitations

routes = [
    {"": [Organizations, {"methods": ["POST"]}]},
    {"/<organization_id>": [Organizations, {"methods": ["PATCH", "DELETE", "GET"]}]},
    {"/roles/<organization_id>": [OrganizationRoles, {"methods": ["POST", "GET"]}]},
    {
        "/roles/<organization_id>/<organization_role_id>": [
            OrganizationRoles,
            {"methods": ["DELETE"]},
        ]
    },
    # Invitation endpoints (org superusers only)
    {
        "/invitations/<organization_id>": [
            OrganizationInvitations,
            {"methods": ["GET", "POST"]},
        ]
    },
    {
        "/invitations/<organization_id>/<organization_invitation_id>": [
            OrganizationInvitations,
            {"methods": ["DELETE"]},
        ]
    },
    # Admin endpoints (superusers only)
    {
        "/admin/<organization_id>": [
            OrganizationsAdmin,
            {"methods": ["PATCH", "DELETE"]},
        ]
    },
    {"/admin": [OrganizationsAdmin, {"methods": ["GET", "POST"]}]},
    {
        "/admin/roles/<organization_id>": [
            OrganizationRolesAdmin,
            {"methods": ["GET", "POST"]},
        ]
    },
    {
        "/admin/roles/<organization_id>/<organization_role_id>": [
            OrganizationRolesAdmin,
            {"methods": ["DELETE"]},
        ]
    },
]
