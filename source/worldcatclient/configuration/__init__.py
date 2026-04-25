from configures import Secrets

import os

secrets = Secrets(
    specification=os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "configuration",
        "required.spec",
    ),
)
