import json
from ipv8.messaging.payload_dataclass import DataClassPayload
from dataclasses import dataclass

@dataclass
class TransferTx(DataClassPayload[1]): # Normal transaction
    sender: str
    recipient: str
    token: str
    amount: int

@dataclass
class AddLiquidityTx(DataClassPayload[2]): # Add liquidity from a provider to token_b
    provider: str
    token_a: str
    amount_a: int
    token_b: str
    amount_b: int

@dataclass
class SwapTx(DataClassPayload[3]): # Swap from token_x to token_y
    trader: str
    from_token: str
    to_token: str
    amount_in: int

@dataclass
class BlockMessage(DataClassPayload[4]):
    index: int
    prev_hash: str
    timestamp: float
    block_hash: str
    tx_data: str # JSON-encoded list of transactions in the block