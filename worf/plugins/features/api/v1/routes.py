from typing import List, Callable, Dict, Tuple, Any

from .features import UserFeatures

routes: List[Dict[str, Tuple[Callable, Dict[str, Any]]]] = [
    {"/user/<user_id>": (UserFeatures, {"methods": ["POST"]})}
]
