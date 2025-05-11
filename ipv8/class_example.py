from ipv8.messaging.payload_dataclass import dataclass
from hashlib import sha256
#from dataclasses import dataclass
import ipv8

name = 'Raul Ernesto Guillen Hernandez'
@dataclass(msg_id = 1)
class ChallengeMessage:
    name: str
    nonce: str


def brute_force_nonce(name, k = 6):
    nonce = 1
    while True:
        candidate = f"{name}{nonce}"
        hash_hex = sha256(candidate.encode('utf-8')).hexdigest()
        if hash_hex.startswith('0'*k):
            return ChallengeMessage(name=name, nonce=str(nonce))
        nonce += 1

#print(brute_force_nonce(name))


#ChallengeMessage(name='Raul Ernesto Guillen Hernandez', nonce='521372')

import os
from asyncio import run
from dataclasses import dataclass

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
#from ipv8.messaging.payload_dataclass import DataClassPayload
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8

import os
from asyncio import run

from ipv8.community import Community
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.peerdiscovery.network import PeerObserver
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8

@dataclass

class MyCommunity(Community):
    community_id = b'harbourspaceuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

    def start_communication(self) -> None:
        print("Called")
        for peer in self.get_peers():
            self.ez_send(peer, ChallengeMessage(name='Raul Ernesto Guillen Hernandez', nonce='521372'))
            print(peer)


    def started(self) -> None:

        self.register_task("start_communication", self.start_communication, interval=5.0, delay=5.0)


async def start_communities() -> None:
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", f"ec{1}.pem")
    builder.add_overlay("MyCommunity", "my peer",
                        [WalkerDefinition(Strategy.RandomWalk,
                                          10, {'timeout': 3.0})],
                        default_bootstrap_defs, {}, [('started',)])
    await IPv8(builder.finalize(),
               extra_communities={'MyCommunity': MyCommunity}).start()


    await run_forever()


run(start_communities())
