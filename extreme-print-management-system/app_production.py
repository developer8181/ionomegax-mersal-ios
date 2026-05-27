"""Production entrypoint — sets EPMS_PRODUCTION unless already configured."""

import os

os.environ.setdefault("EPMS_PRODUCTION", "1")
os.environ.setdefault("EPMS_REQUIRE_AUTH", "1")
os.environ.setdefault("EPMS_ANONYMIZE_DOCS", "1")

from epms.server import run


if __name__ == "__main__":
    run()
