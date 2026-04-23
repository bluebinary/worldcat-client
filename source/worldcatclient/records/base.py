from worldcatclient.logging import logger
from classicist import aliased
from typing import Iterator

logger = logger.getChild(__name__)


class WorldCatData(metaclass=aliased):
    """The WorldCatData class represents data retrieved from WorldCat."""

    _data: dict[str, object] = None

    def __init__(self, data: dict[str, object] = None, **kwargs: dict[str, object]):
        """Support initialising the WorldCatData class."""

        if data is None:
            data = {}
        elif not isinstance(data, dict):
            raise TypeError(
                "The 'data' argument, if specified, must reference a dictionary!"
            )

        self._data: dict[str, object] = data

        for key, value in kwargs.items():
            self._data[key] = value

    def __str__(self) -> str:
        """Return a string representation of the WorldCatData instance for logging."""

        return f"<{self.__class__.__name__}()>"

    def __repr__(self) -> str:
        """Return a string representation of the WorldCatData instance for debugging."""

        return f"<{self.__class__.__name__}() object at {hex(id(self))}>"

    def __iter__(self) -> Iterator[tuple[str, object]]:
        """Support iterating over the WorldCatData instance's data."""

        for key, value in self._data.items():
            yield key, value

    def __getattr__(self, name: str) -> object:
        """Support returning a named attribute from the WorldCatData class."""

        if name.startswith("_"):
            return super().__getattr__(name)
        elif name in self._data:
            return self._data[name]
        else:
            raise AttributeError(
                f"No '{name}' attribute is available on the '{self.__class__.__name__}' class!"
            )

    @property
    def data(self) -> dict[str, object]:
        """Return a copy of the WorldCatData class' data."""

        return dict(self._data)


__all__ = [
    "WorldCatData",
]
