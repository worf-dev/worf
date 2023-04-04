from typing import List, Tuple, Callable, Dict, Any
from .resources.hooks import Hooks

routes: List[Dict[str, Tuple[Callable, Dict[str, Any]]]] = [
    # Hooks
    {"/hooks": (Hooks, {"methods": ["GET", "POST"]})}
]
