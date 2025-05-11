from dataclasses import dataclass
from ipv8.messaging.payload_dataclass import DataClassPayload


@dataclass
class GossipData(DataClassPayload[1]):
    origin: int
    seq_no: int
    content: str

@dataclass
class GossipQuery(DataClassPayload[2]):
    nonce: int