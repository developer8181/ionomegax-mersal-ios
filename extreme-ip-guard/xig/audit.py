"""Tamper-evident audit chain helpers.

The audit module provides a pure :class:`AuditChain` class that knows how to
extend a hash chain and verify it. The storage layer persists the resulting
hashes alongside the row; this module is intentionally storage-agnostic so
the same logic can be reused in tests, exports, and integrity checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .core import canonical_json
from .crypto import chain_hash, merkle_root, sha256_hex


GENESIS_HASH = sha256_hex("xig:genesis")


@dataclass(frozen=True)
class ChainedRecord:
    """A record after it has been incorporated into the audit chain."""

    prev_hash: str
    chain_hash: str
    payload: dict


class AuditChain:
    """In-memory representation of a hash chain.

    The class is small enough to copy when needed and stateless apart from
    ``last_hash``. Persisting the chain is done by writing
    :attr:`ChainedRecord.payload`, :attr:`ChainedRecord.prev_hash`, and
    :attr:`ChainedRecord.chain_hash` to durable storage.
    """

    def __init__(self, last_hash: str | None = None) -> None:
        self._last = last_hash or GENESIS_HASH

    @property
    def last_hash(self) -> str:
        return self._last

    def append(self, record: dict) -> ChainedRecord:
        prev = self._last
        record_no_hashes = {k: v for k, v in record.items() if k not in {"chain_hash", "prev_hash"}}
        new_hash = chain_hash(prev, record_no_hashes)
        self._last = new_hash
        return ChainedRecord(prev_hash=prev, chain_hash=new_hash, payload=record_no_hashes)

    @staticmethod
    def verify(records: Iterable[dict]) -> tuple[bool, int]:
        """Replay a sequence of stored records.

        Returns ``(ok, broken_at_index)``. ``broken_at_index`` is the index
        of the first record where the recomputed hash disagrees with the
        stored one, or ``-1`` when the chain is intact.
        """

        previous = GENESIS_HASH
        for index, record in enumerate(records):
            stored_prev = record.get("prev_hash", "")
            stored_hash = record.get("chain_hash", "")
            if stored_prev != previous:
                return False, index
            recomputed = chain_hash(previous, _strip_hashes(record))
            if recomputed != stored_hash:
                return False, index
            previous = stored_hash
        return True, -1

    @staticmethod
    def checkpoint(records: Iterable[dict]) -> dict:
        """Produce a Merkle-root checkpoint over an iterable of stored records.

        The output is suitable for publishing to a separate channel (email
        digest, off-host log shipper, blockchain receipt, …) and later used
        as proof that no entries were tampered with.
        """

        hashes = [record.get("chain_hash", "") for record in records]
        return {
            "count": len(hashes),
            "merkle_root": merkle_root(hashes),
            "first": hashes[0] if hashes else "",
            "last": hashes[-1] if hashes else "",
        }


def _strip_hashes(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in {"chain_hash", "prev_hash"}}


def canonical_record(payload: dict) -> str:
    """Re-export of :func:`xig.core.canonical_json` for audit consumers."""

    return canonical_json(payload)
