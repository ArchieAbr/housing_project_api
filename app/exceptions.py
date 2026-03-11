class CustomAPIException(Exception):
    def __init__(self, name: str, detail: str, status_code: int = 400):
        self.name = name
        self.detail = detail
        self.status_code = status_code