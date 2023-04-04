from flask import request

from worf.api.resource import Resource
from worf.settings import settings
from ...tasks import process_hook
import hmac, hashlib


def sign(key, data):
    h = hmac.new(key.encode("ascii"), data, hashlib.sha256)
    return h.hexdigest()


class Hooks(Resource):

    """
    Receive hooks from Stripe
    """

    def post(self):
        """
        Receive hooks from Stripe.
        """
        signing_keys = settings.get("stripe.hook_signing_keys", [])
        try:
            signature_parts = request.headers["Stripe-Signature"].split(",")
        except KeyError:
            return {"message": "must be signed"}, 400
        t = None
        signature = None
        for part in signature_parts:
            if part.startswith("t="):
                t = part[2:]
            elif part.startswith("v1="):
                signature = part[3:]
                # we check the signature against all signing keys
                for signing_key in signing_keys:
                    generated_signature = sign(
                        signing_key, t.encode("ascii") + b"." + request.get_data()
                    )
                    if generated_signature == signature:
                        # if the signature matches we break out of the loop
                        break
                else:
                    # the signature did not match
                    continue
                # the signature matched, we break out of the loop
                break
        else:
            # no signature matched
            return {"message": "missing or mismatched signature"}, 400
        # we asynchronously process the hook data
        settings.delay(process_hook, data=request.json)
        return ({}, 200)
