from worldcatclient.logging import logger

logger = logger.getChild(__name__)


class WorldCatRecord(object):
    """The WorldCatRecord class represents a search result record's data."""

    def __init__(self, data: dict[str, object]):
        if not isinstance(data, dict):
            raise TypeError("The 'data' argument must reference a dictionary value!")

        self._data = data

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}({self.title} / {self.creator} / {self.date} / {self.oclc})>"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.title} / {self.creator} / {self.date} / {self.oclc}) object at {hex(id(self))}>"

    def __getattr__(self, name: str) -> object:
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
        return self._data

    @property
    def oclc(self) -> str | None:
        return self._data.get("oclcNumber")

    @property
    def creator(self) -> str | None:
        return self._data.get("creator")

    @property
    def isbns(self) -> list[str]:
        return self._data.get("isbns") or []


__all__ = [
    "Record",
]
