from .features import UserFeatures

routes = [{"/user/<user_id>": (UserFeatures, {"methods": ["POST"]})}]
