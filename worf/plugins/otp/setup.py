from .models import OTP
from .api.v1.routes import routes

config = {"models": [OTP], "providers": {"login": None}, "endpoints": routes}
