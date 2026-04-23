from worldcatclient.logging import logger
from worldcatclient.records.base import WorldCatData
from worldcatclient.records.cataloging import WorldCatInfo
from classicist import alias
from fluently import flist

logger = logger.getChild(__name__)


class WorldCatRecord(WorldCatData):
    """The WorldCatRecord class represents a publication's data."""

    def __str__(self) -> str:
        """Return a string representation of the WorldCatRecord instance for logging."""

        return f"<{self.__class__.__name__}({self.title} / {self.creator} / {self.date} / {self.oclc})>"

    def __repr__(self) -> str:
        """Return a string representation of the WorldCatRecord instance for debugging."""

        return f"<{self.__class__.__name__}({self.title} / {self.creator} / {self.date} / {self.oclc}) object at {hex(id(self))}>"

    @property
    @alias("oclc", "number")
    def oclc_number(self) -> str | None:
        """Return the publication's OCLC number."""

        if isinstance(oclc_number := self._data.get("oclcNumber"), str):
            return oclc_number

    @property
    def title(self) -> str | None:
        """Return the publication's title."""

        if isinstance(title := self._data.get("title"), str):
            return title

    @property
    def creator(self) -> str | None:
        """Return the publication's creator."""

        if isinstance(creator := self._data.get("creator"), str):
            return creator

    @property
    @alias("date")
    def machine_readable_date(self) -> str | None:
        """Return the publication's machine readable date."""

        if isinstance(date := self._data.get("machineReadableDate"), str):
            return date

    @property
    def language(self) -> str | None:
        """Return the publication's ISO 639-3 language code."""

        if isinstance(language := self._data.get("language"), str):
            return language

    @property
    @alias("format_general")
    def general_format(self) -> str | None:
        """Return the publication's general format name."""

        if isinstance(format := self._data.get("generalFormat"), str):
            return format

    @property
    @alias("format_specific", "format")
    def specific_format(self) -> str | None:
        """Return the publication's specific format name."""

        if isinstance(format := self._data.get("specificFormat"), str):
            return format

    @property
    def publisher(self) -> str | None:
        """Return the publication's publisher."""

        if isinstance(publisher := self._data.get("publisher"), str):
            return publisher

    @property
    def publication_place(self) -> str | None:
        """Return the publication's publication place."""

        if isinstance(publication_place := self._data.get("publicationPlace"), str):
            return publication_place

    @property
    def isbns(self) -> flist[str]:
        """Return the publication's associated ISBNs."""

        if isinstance(isbns := self._data.get("isbns"), list):
            return flist(isbns)
        else:
            return flist()

    @property
    @alias("cataloging", "cataloguing_info", "cataloguing")
    def cataloging_info(self) -> WorldCatInfo | None:
        """Return the publication's cataloguing info."""

        if isinstance(data := self._data.get("catalogingInfo"), dict):
            return WorldCatInfo(data=data)


__all__ = [
    "WorldCatRecord",
]
