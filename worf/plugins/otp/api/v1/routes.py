prefix = "/v1"

import logging

logger = logging.getLogger(__name__)

from .resources.otp import OTP, ActivateOTP

routes = [
    {"/otp/activate": [ActivateOTP, {"methods": ["POST"]}]},
    {"/otp": [OTP, {"methods": ["POST", "DELETE", "PUT"]}]},
]
