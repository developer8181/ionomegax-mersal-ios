"""Extreme IP Guard - next-generation endpoint protection and DLP reference core.

This package is a self-contained Python reference implementation that proves the
architecture documented in ``docs/EXTREME_ARCHITECTURE_AR.md``. It uses only the
Python standard library so it can run anywhere without external dependencies.

Production deployments are expected to replace individual components
(agent, storage backend, search index) with hardened implementations while
keeping the same domain model.
"""

__all__ = [
    "core",
    "crypto",
    "policies",
    "detection",
    "audit",
    "storage",
    "agents",
    "server",
]
