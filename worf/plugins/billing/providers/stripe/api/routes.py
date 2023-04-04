from .resources.hooks import Hooks

routes = [
    # Hooks
    {"/hooks": (Hooks, {"methods": ["GET", "POST"]})}
]
