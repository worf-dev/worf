from .resources.user import (
    Login,
    Logout,
    Signup,
    SignupRequests,
    ConfirmSignup,
    UserProfile,
    Invitations,
    Users,
    UserAccessTokens,
    SuperUserAccessTokens,
    AccessTokenScopes,
    EMailChange,
)

from .resources.block_email import BlockEMail
from .resources.client_settings import ClientSettings

routes = [
    {"/login/<provider_name>": [Login, {"methods": ["POST"]}]},
    {"/login/<provider_id>": [Login, {"methods": ["DELETE"]}]},
    {"/login": [Login, {"methods": ["GET"]}]},
    {"/logout": [Logout, {"methods": ["POST"]}]},
    {"/signup/<provider_name>": [Signup, {"methods": ["POST"]}]},
    {"/signup-requests": [SignupRequests, {"methods": ["GET"]}]},
    {
        "/signup-requests/<request_id>": [
            SignupRequests,
            {"methods": ["POST", "DELETE"]},
        ]
    },
    {"/confirm-signup": [ConfirmSignup, {"methods": ["GET"]}]},
    {"/user": [UserProfile, {"methods": ["GET", "PATCH"]}]},
    {"/block-email": [BlockEMail, {"methods": ["GET"]}]},
    {"/access-tokens": [UserAccessTokens, {"methods": ["POST", "GET"]}]},
    # access token management (superusers only)
    {"/access-token-scopes": [AccessTokenScopes, {"methods": ["GET"]}]},
    {"/access-tokens/<access_token_id>": [UserAccessTokens, {"methods": ["DELETE"]}]},
    {"/change-email": [EMailChange, {"methods": ["POST", "PUT"]}]},
    # user management (superusers only)
    {"/users": [Users, {"methods": ["GET", "POST"]}]},
    {"/users/<user_id>": [Users, {"methods": ["GET", "PATCH", "DELETE"]}]},
    {
        "/users/<user_id>/access-tokens": [
            SuperUserAccessTokens,
            {"methods": ["POST", "GET"]},
        ]
    },
    # invitations (superusers only)
    {"/invitations": [Invitations, {"methods": ["GET", "POST"]}]},
    {"/invitations/<invitation_id>": [Invitations, {"methods": ["GET", "DELETE"]}]},
    # settings
    {"/settings": [ClientSettings, {"methods": ["GET"]}]},
]
