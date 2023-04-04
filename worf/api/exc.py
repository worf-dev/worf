class LoginError(BaseException):
    def __init__(self, message, errors):
        super().__init__()
        self.message = message
        self.errors = errors
