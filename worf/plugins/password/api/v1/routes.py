from .resources import PasswordChange, PasswordReset

routes = [
    {"/change": [PasswordChange, {"methods": ["POST"]}]},
    {"/reset": [PasswordReset, {"methods": ["POST", "PUT"]}]},
]
