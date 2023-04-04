from worf.settings import settings
from worf.models import EMailRequest, CryptoToken
from worf.api.resource import Resource

from flask import request


class BlockEMail(Resource):
    def get(self):
        code = request.args.get("code")
        if not code:
            return {"message": self.t("block-email.code-missing")}, 400
        try:
            data = settings.decrypt(code.encode("ascii"), ttl=60 * 60 * 24)
        except:
            return {"message": self.t("block-email.invalid-or-expired-code")}, 400
        with settings.session() as session:
            hash = CryptoToken.get_hash(code)
            token = CryptoToken.get_or_create(session, hash)
            if token.used:
                return {"message": self.t("block-email.token-already-used")}, 400
            token.used = True
            req = EMailRequest.get_or_create(
                session, data["purpose"], sha256=data["sha256"]
            )
            if req.blocked:
                return {"message": self.t("block-email.already-blocked")}, 200
            req.blocked = True
        return {"message": self.t("success")}, 200
