from enumerific import Enumeration, anno


class WorldCatScope(Enumeration):
    """The WorldCatScope enumeration lists scopes for the WorldCat API."""

    SearchAPI = anno(
        value="wcapi",
        description="WorldCat Search API",
    )

    AcquisitionsAPI = anno(
        value="WMS_ACQ",
        description="WMS Acquisitions API (Version 1)",
    )

    VendorInformationCenterAPI = anno(
        value="WMS_VIC",
        description="WMS Vendor Information Center API",
    )

    MetadataAPI = anno(
        value="WorldCatMetadataAPI",
        description="WorldCat Metadata API",
    )

    @property
    def mnemonic(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class WorldCatOrderingSearchAPI(Enumeration):
    """The WorldCatOrderingSearchAPI enumeration lists the supported sort order options
    for the Search API results."""

    Library = anno("library")

    Recency = anno("recency")

    BestMatch = anno("bestMatch")

    Creator = anno("creator")

    PublicationDateAsc = anno("publicationDateAsc")

    PublicationDateDesc = anno("publicationDateDesc")

    MostWidelyHeld = anno("mostWidelyHeld")

    Title = anno("title")


__all__ = [
    "WorldCatScope",
    "WorldCatOrderingSearchAPI",
]
