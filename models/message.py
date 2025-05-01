from ipv8.messaging.payload_dataclass import dataclass


@dataclass(msg_id=1)
class Message:
    public_key: bytes
    signature: bytes
    nonce: bytes
