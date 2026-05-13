class ValidateTokenResponse:
    def __init__(self, valid=False, user_id="", error=""):
        self.valid = valid
        self.user_id = user_id
        self.error = error


class GetUserInfoResponse:
    def __init__(self, user_id="", username="", email="", is_active=False):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.is_active = is_active
