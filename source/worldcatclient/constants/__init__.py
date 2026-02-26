# Default WorldCat API endpoint
WORLDCAT_API_ENDPOINT = "https://americas.discovery.api.oclc.org"

# Default OCLC OAuth authentication endpoint
OCLC_AUTHENTICATION_ENDPOINT = "https://oauth.oclc.org/token"

# Default timeouts for connection and read (in seconds)
DEFAULT_TIMEOUTS = (30, 60)


__all__ = [
    "WORLDCAT_API_ENDPOINT",
    "OCLC_AUTHENTICATION_ENDPOINT",
    "DEFAULT_TIMEOUTS",
]
