class DomainException(Exception):
    """Raised when a domain invariant is violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class NotFoundException(Exception):
    """Raised when an aggregate cannot be found."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
