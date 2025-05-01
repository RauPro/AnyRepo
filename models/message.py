from ipv8.messaging.payload_dataclass import dataclass
from ipv8.keyvault.keys import PublicKey


@dataclass(msg_id=1)
class Message:
    public_key: bytes
    signature: bytes
    nonce: bytes
