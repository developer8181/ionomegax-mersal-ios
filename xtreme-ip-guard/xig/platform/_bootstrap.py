"""Load platform-specific collectors."""

from . import darwin as _darwin  # noqa: F401
from . import linux as _linux  # noqa: F401
from . import windows as _windows  # noqa: F401
