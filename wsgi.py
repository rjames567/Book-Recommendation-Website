# ------------------------------------------------------------------------------
# Project imports
# ------------------------------------------------------------------------------
import environ_manipulation

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
class Middleware:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def __iter__(self):
        environ_manipulation.application.add_target(self.environ)
        match self.environ["TARGET_APPLICATION"]:
            case "account":
                application = AccountApplication(self.environ, self.start)
                yield application()
            case _:
                response_headers = [("Content-type", "text/plain")]
                self.start("200 OK", response_headers)
                yield "Page Not Found".encode("utf-8")

# ------------------------------------------------------------------------------
# Sub-Applications
# ------------------------------------------------------------------------------
class AccountApplication:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response

    def __call__(self):
        response_headers = [("Content-type", "text/plain")]
        self.start("200 OK", response_headers)
        return "Account".encode("utf-8")