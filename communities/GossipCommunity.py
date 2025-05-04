from ipv8.community import Community, CommunitySettings
from ipv8.lazy_community import lazy_wrapper
from ipv8.types import Peer

from models.models import GossipData, GossipQuery


class GossipCommunity(Community):
    community_id = b"randomteamwithrusian"
    gossip_mode = "push"

    def __init__(self, settings: CommunitySettings):
        super().__init__(settings)
        self.known_messages = {}    # Map (origin, seq_no) -> content
        self.sent_count = 0         # Total messages sent by this peer
        self.duplicate_count = 0    # Number of duplicate messages received
        self.add_message_handler(GossipData, self.on_gossip_data)
        self._origin_seq = 0

    @lazy_wrapper(GossipData)
    def on_gossip_data(self, peer: Peer, payload: GossipData) -> None:
        msg_id = (payload.origin, payload.seq_no)
        if msg_id in self.known_messages:
            # Duplicate message received
            self.duplicate_count += 1
            return
        self.known_messages[msg_id] = payload.content
        if self.gossip_mode in ("push", "hybrid"):
            for neighbor in self.get_peers():
                if neighbor == peer:
                    continue
                self.ez_send(neighbor, GossipData(payload.origin, payload.seq_no, payload.content))
                self.sent_count += 1
        return


    def started(self) -> None:
        if self.gossip_mode in ("pull", "hybrid"):
            async def query_neighbors_periodically():
                neighbors = self.get_peers()
                if neighbors:
                    target = neighbors[0]
                    self.ez_send(target, GossipQuery(nonce=self._origin_seq))
                    self.sent_count += 1
                    self._origin_seq += 1
            self.register_task("gossip_pull_task", query_neighbors_periodically, interval=2.0, delay=2.0)