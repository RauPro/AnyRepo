from dataclasses import dataclass
import hashlib, time

@dataclass
class Block:
    index: int
    prev_hash: str
    timestamp: float
    transactions: list
    hash: str = ""

    def compute_hash(self):
        """Compute SHA-256 hash of the block’s contents (index, prev_hash, timestamp, transactions)."""
        block_string = f"{self.index}{self.prev_hash}{self.timestamp}{self.transactions}"
        self.hash = hashlib.sha256(block_string.encode()).hexdigest()
        return self.hash