from .models import Features, clean_db
from .api.v1.routes import routes
from .providers.profile import features_profile

config = {
    "clean_db": clean_db,
    "api": [{"routes": routes, "version": "v1"}],
    "models": [Features],
    "providers": {"profile": features_profile},
}
