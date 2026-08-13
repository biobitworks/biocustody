from __future__ import annotations
import hashlib

def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def leaf_hash(text: str) -> bytes:
    return _h(b"\x00" + text.encode("utf-8"))

def node_hash(left: bytes, right: bytes) -> bytes:
    return _h(b"\x01" + left + right)

def merkle_root_hex(items: list[str]) -> str:
    if not items:
        return hashlib.sha256(b"").hexdigest()
    level = [leaf_hash(x) for x in items]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [node_hash(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return level[0].hex()

class MMRRootAccumulator:
    """
    MMR-style peak accumulator for an append-only root summary.

    This implements append + peak bagging only. It deliberately does NOT claim
    to provide standardized MMR inclusion/consistency proofs.
    """
    def __init__(self):
        self.peaks: list[tuple[int, bytes]] = []
        self.count = 0

    def append(self, item_digest: str) -> str:
        height = 0
        current = leaf_hash(item_digest)
        while self.peaks and self.peaks[-1][0] == height:
            _, left = self.peaks.pop()
            current = node_hash(left, current)
            height += 1
        self.peaks.append((height, current))
        self.count += 1
        return self.root_hex()

    def root_hex(self) -> str:
        if not self.peaks:
            return hashlib.sha256(b"").hexdigest()
        acc = self.peaks[0][1]
        for _, peak in self.peaks[1:]:
            acc = node_hash(acc, peak)
        return acc.hex()
