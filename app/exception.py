class InvalidAccessToken(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ExpiredAccessToken(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class OutTermAccessToken(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)        

class NoHeaderInfo(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class NotFoundProfile(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SendEmailFail(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
