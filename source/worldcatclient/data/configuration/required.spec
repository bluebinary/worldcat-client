# WorldCat Client: Required Runtime Configuration Specification
# This file lists the environment variables required by the application, and defines the
# acceptable format for each variables' value. The runtime environment must provide the
# environment variables listed below, and the value of each must conform to the regexes.

# WorldCat API Client Configuration
WORLDCAT_API_ENDPOINT=(http(s)?://[a-z0-9\-]+(?:\.[a-z0-9\-]+){1,}(\:[0-9]{1,5})?(/[\w\-\_]+)*/?)
WORLDCAT_API_TOKEN=([0-9a-f]{32})
WORLDCAT_API_TIMEOUT=([0-9]+(\.[0-9]+)?)
