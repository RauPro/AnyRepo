import json
from ipv8.messaging.payload_dataclass import DataClassPayload
from dataclasses import dataclass

@dataclass
class TransferTx(DataClassPayload[1]):
    sender: str
    recipient: str
    token: str
    amount: int

@dataclass
class AddLiquidityTx(DataClassPayload[2]):
    provider: str
    token_a: str
    amount_a: int
    token_b: str
    amount_b: int

@dataclass
class SwapTx(DataClassPayload[3]):
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
    tx_data: str