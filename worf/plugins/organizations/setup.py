from .models import Organization, OrganizationRole, clean_db
from .api.v1.routes import routes
from .providers.profile import organization_profile
from .hooks import confirm_invite_and_setup_role
from .cli import organizations

config = {
    "clean_db": clean_db,
    "api": [{"routes": routes, "version": "v1"}],
    "models": [Organization, OrganizationRole],
    "commands": [organizations],
    "providers": {"profile": organization_profile},
    "hooks": {"invitation.confirm": confirm_invite_and_setup_role},
}
