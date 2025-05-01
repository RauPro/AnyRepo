from ipv8.community import Community, CommunitySettings
from ipv8.peer import Peer
from ipv8.lazy_community import lazy_wrapper
from ipv8.keyvault.crypto import ECCrypto
from ipv8.messaging.payload_headers import BinMemberAuthenticationPayload

from models.message import Message
from data.community_id import community_id


class OurCommunity(Community):
    community_id = community_id

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.add_message_handler(Message, self.on_message)

    def on_peer_added(self, peer: Peer) -> None:
        print(
            f"Local peer {self.my_peer.mid.hex()[:8]} discovered new peer {peer.mid.hex()[:8]}"
        )

    def on_peer_removed(self, peer: Peer) -> None:
        print(f"Local peer {self.my_peer.mid.hex()[:8]} lost peer {peer.mid.hex()[:8]}")
        pass

    def started(self) -> None:
        self.network.add_peer_observer(self)

        print(f"Local peer {self.my_peer.mid.hex()[:8]} started successfully")

        data = b"hello world!"

        public_key = self.my_peer.public_key.key_to_bin()
        private_key = self.my_peer.key

        crypto = ECCrypto()
        signature = crypto.create_signature(private_key, data)

        async def start_communication() -> None:
            for p in self.get_peers():
                self.ez_send(p, Message(public_key, signature, data))

        self.register_task(
            "start_communication", start_communication, interval=5.0, delay=5.0
        )

    @lazy_wrapper(Message)
    def on_message(self, peer: Peer, payload: Message) -> None:
        print(
            f"Local peer {self.my_peer.mid.hex()[:8]} received message from {peer.mid.hex()[:8]}: {payload}"
        )

        if not self._verify_signature(
            BinMemberAuthenticationPayload(payload.public_key), payload.nonce
        ):
            print(
                f"Local peer {self.my_peer.mid.hex()[:8]} received invalid message from {peer.mid.hex()[:8]}: {payload}"
            )
            return

        print(
            f"Local peer {self.my_peer.mid.hex()[:8]} received valid message from {peer.mid.hex()[:8]}: {payload}"
        )
