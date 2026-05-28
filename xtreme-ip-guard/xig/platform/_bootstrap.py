# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Load platform-specific collectors."""

from . import darwin as _darwin  # noqa: F401
from . import linux as _linux  # noqa: F401
from . import windows as _windows  # noqa: F401
