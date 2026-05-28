# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Legal notice and authorship — Extreme Cyber Security platform."""

from __future__ import annotations

COPYRIGHT_YEARS = "2009–2026"

CREDITS_AR = {
    "title": "معلومات عن النظام",
    "product_line": "منصة Extreme Cyber Security · Extreme Security Fabric",
    "authorship": (
        "تم تصميم وبرمجة هذا النظام بواسطة المهندس محمود راسم بياري، "
        "مهندس أنظمة الحماية — رام الله، فلسطين."
    ),
    "company": (
        "مؤسس شركة Extreme Technology (إكستريم تكنولوجي) — رام الله، فلسطين."
    ),
    "rights": f"جميع الحقوق محفوظة © {COPYRIGHT_YEARS}",
    "notice": (
        "يُحظر نسخ أو توزيع أو تعديل أي جزء من هذا البرنامج دون إذن كتابي "
        "من صاحب الحقوق أو الشركة المالكة."
    ),
}

CREDITS_EN = {
    "title": "About the System",
    "product_line": "Extreme Cyber Security Platform · Extreme Security Fabric",
    "authorship": (
        "Designed and developed by Eng. Mahmoud Rasem Bayari, "
        "Cybersecurity Systems Engineer — Ramallah, Palestine."
    ),
    "company": (
        "Founder of Extreme Technology Company — Ramallah, Palestine."
    ),
    "rights": f"All rights reserved © {COPYRIGHT_YEARS}",
    "notice": (
        "No part of this software may be reproduced, distributed, or modified "
        "without written permission from the copyright holder."
    ),
}

SOURCE_HEADER = f"""\
# Copyright (c) {COPYRIGHT_YEARS} Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""


def system_about(*, version: str = "2.0.0") -> dict:
    """Payload for /api/system/about and Command Center modal."""
    return {
        "product": "Extreme Cyber Security Platform",
        "operating_system": "Extreme Cyber Security OS",
        "version": version,
        "vendor": "Extreme Technology Company",
        "powered_by": "Extreme Technology Company",
        "location": "Ramallah, Palestine",
        "engineer": {
            "name_ar": "محمود راسم بياري",
            "name_en": "Mahmoud Rasem Bayari",
            "title_ar": "مهندس أنظمة الحماية",
            "title_en": "Cybersecurity Systems Engineer",
        },
        "copyright_years": COPYRIGHT_YEARS,
        "ar": CREDITS_AR,
        "en": CREDITS_EN,
        "footer_ar": (
            f"© {COPYRIGHT_YEARS} Extreme Technology · المهندس محمود راسم بياري · رام الله"
        ),
        "footer_en": (
            f"© {COPYRIGHT_YEARS} Extreme Technology · Eng. Mahmoud Rasem Bayari · Ramallah"
        ),
    }
