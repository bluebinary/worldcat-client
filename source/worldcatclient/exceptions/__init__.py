class WorldCatClientError(RuntimeError):
    pass


class WorldCatRequestError(WorldCatClientError):
    def __init__(self, message: str, /, status_code: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self._status_code = status_code

    @property
    def status_code(self) -> int:
        return self._status_code


class WorldCatAuthenticationError(WorldCatRequestError):
    pass


class WorldCatResponseError(WorldCatRequestError):
    pass


__all__ = [
    "WorldCatClientError",
    "WorldCatRequestError",
    "WorldCatAuthenticationError",
    "WorldCatResponseError",
]
