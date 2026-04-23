from worldcatclient.logging import logger
from worldcatclient.records.base import WorldCatData
from classicist import alias

logger = logger.getChild(__name__)


class WorldCatInfo(WorldCatData):
    """The WorldCatInfo class represents a publication's cataloging info."""

    @property
    @alias("agency")
    def cataloging_agency(self) -> str | None:
        """Return the publication's cataloguing agency."""

        if isinstance(agency := self._data.get("catalogingAgency"), str):
            return agency

    @property
    @alias("language")
    def cataloging_language(self) -> str | None:
        """Return the publication's cataloguing language."""

        if isinstance(language := self._data.get("catalogingLanguage"), str):
            return language

    @property
    @alias("level")
    def level_of_cataloging(self) -> str | None:
        """Return the publication's level of cataloging."""

        if isinstance(level := self._data.get("levelOfCataloging"), str):
            return level

    @property
    def transcribing_agency(self) -> str | None:
        """Return the publication's transcribing agency."""

        if isinstance(agency := self._data.get("transcribingAgency"), str):
            return agency


__all__ = [
    "WorldCatInfo",
]
