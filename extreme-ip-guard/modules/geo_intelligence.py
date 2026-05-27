"""
Extreme IP Guard - Geolocation Intelligence Module
Provides IP geolocation with country risk assessment and
geographic policy enforcement.
"""

import ipaddress
from typing import Dict, Optional, Tuple

# Pre-populated threat intelligence for common ranges, supplemented
# by GeoIP database lookups when available.

COUNTRY_RISK_SCORES: Dict[str, float] = {
    "US": 10, "GB": 10, "DE": 8, "FR": 9, "CA": 8, "AU": 8,
    "JP": 7, "KR": 12, "BR": 15, "IN": 14, "RU": 25, "CN": 22,
    "IR": 30, "KP": 35, "NG": 20, "UA": 18, "RO": 16, "VN": 14,
    "ID": 13, "PK": 18, "BD": 15, "PH": 12, "TH": 11,
}

# Well-known datacenter/cloud provider ranges (simplified)
KNOWN_DATACENTER_RANGES = [
    ("13.0.0.0/8", "Amazon AWS"),
    ("34.0.0.0/8", "Google Cloud"),
    ("40.0.0.0/8", "Microsoft Azure"),
    ("104.16.0.0/12", "Cloudflare"),
    ("172.64.0.0/13", "Cloudflare"),
    ("198.41.128.0/17", "Cloudflare"),
    ("151.101.0.0/16", "Fastly"),
    ("185.199.108.0/22", "GitHub"),
    ("192.30.252.0/22", "GitHub"),
]


class GeoIntelligence:
    """
    Geographic intelligence for IP addresses:
    - Country/city resolution
    - Risk scoring by geography
    - Datacenter detection
    - Geographic fencing
    - Travel pattern analysis
    """

    def __init__(self):
        self._geoip_reader = None
        self._blocked_countries: set = set()
        self._allowed_countries: set = set()
        self._geo_cache: Dict[str, dict] = {}

    def lookup(self, ip_str: str) -> dict:
        if ip_str in self._geo_cache:
            return self._geo_cache[ip_str]

        result = {
            "ip": ip_str,
            "country": None,
            "country_name": None,
            "city": None,
            "latitude": None,
            "longitude": None,
            "timezone": None,
            "asn": None,
            "org": None,
            "isp": None,
            "is_datacenter": False,
            "datacenter_name": None,
            "risk_score": 0.0,
            "geo_blocked": False,
        }

        try:
            addr = ipaddress.ip_address(ip_str)
            if addr.is_private or addr.is_loopback:
                result["country"] = "LOCAL"
                result["country_name"] = "Local Network"
                result["risk_score"] = 0.0
                self._geo_cache[ip_str] = result
                return result
        except ValueError:
            return result

        dc_info = self._check_datacenter(ip_str)
        if dc_info:
            result["is_datacenter"] = True
            result["datacenter_name"] = dc_info

        if self._geoip_reader:
            try:
                geo = self._geoip_reader.city(ip_str)
                result["country"] = geo.country.iso_code
                result["country_name"] = geo.country.name
                result["city"] = geo.city.name
                result["latitude"] = geo.location.latitude
                result["longitude"] = geo.location.longitude
                result["timezone"] = geo.location.time_zone
            except Exception:
                pass

        if result["country"]:
            result["risk_score"] = COUNTRY_RISK_SCORES.get(result["country"], 10.0)
            if self._blocked_countries and result["country"] in self._blocked_countries:
                result["geo_blocked"] = True
            if self._allowed_countries and result["country"] not in self._allowed_countries:
                result["geo_blocked"] = True

        self._geo_cache[ip_str] = result
        return result

    def _check_datacenter(self, ip_str: str) -> Optional[str]:
        try:
            addr = ipaddress.ip_address(ip_str)
            for network_str, name in KNOWN_DATACENTER_RANGES:
                if addr in ipaddress.ip_network(network_str, strict=False):
                    return name
        except ValueError:
            pass
        return None

    def set_geo_policy(
        self,
        blocked_countries: set = None,
        allowed_countries: set = None,
    ):
        if blocked_countries is not None:
            self._blocked_countries = blocked_countries
        if allowed_countries is not None:
            self._allowed_countries = allowed_countries
        self._geo_cache.clear()

    def check_geo_fence(self, ip_str: str) -> dict:
        info = self.lookup(ip_str)
        return {
            "ip": ip_str,
            "country": info["country"],
            "allowed": not info["geo_blocked"],
            "reason": "geo_blocked" if info["geo_blocked"] else "allowed",
            "risk_score": info["risk_score"],
        }

    def get_country_stats(self) -> dict:
        countries = {}
        for info in self._geo_cache.values():
            c = info.get("country")
            if c:
                countries[c] = countries.get(c, 0) + 1
        return {
            "total_cached": len(self._geo_cache),
            "countries": countries,
            "blocked_countries": list(self._blocked_countries),
            "allowed_countries": list(self._allowed_countries),
        }

    def clear_cache(self):
        self._geo_cache.clear()


geo_intelligence = GeoIntelligence()
