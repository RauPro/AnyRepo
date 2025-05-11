import asyncio
import os
import json
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8_service import IPv8

from communities.GossipCommunity import GossipCommunity
from models.models import GossipData


async def start_communities(num_peers: int, topology: str, gossip_mode: str, duration: float = 30.0):
    target_peers = 3 if topology == "sparse" else 15
    print(f"Starting simulation: {num_peers} peers, topology={topology}, mode={gossip_mode}.")
    ipv8_services = []
    communities = []
    for i in range(1, num_peers + 1):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key(f"peer{i}", "medium", f"ec{i}.pem")
        walkers = [WalkerDefinition(Strategy.RandomWalk, target_peers, {'timeout': 3.0})]
        builder.add_overlay(
            "GossipCommunity",
            f"peer{i}",
            walkers,
            default_bootstrap_defs,
            {},
            [("started",)],
        )
        ipv8 = IPv8(builder.finalize(), extra_communities={"GossipCommunity": GossipCommunity})
        await ipv8.start()
        comm = next(c for c in ipv8.overlays if isinstance(c, GossipCommunity))
        comm.gossip_mode = gossip_mode
        comm.peer_id = i
        communities.append(comm)
        ipv8_services.append(ipv8)
    await asyncio.sleep(5.0)
    if communities:
        origin = communities[0]
        origin._origin_seq += 1
        seq = origin._origin_seq
        content = f"Hello from peer{origin.peer_id}"
        origin.known_messages[(origin.peer_id, seq)] = content
        if gossip_mode in ("push", "hybrid"):
            for nbr in origin.get_peers():
                origin.ez_send(nbr, GossipData(origin.peer_id, seq, content))
                origin.sent_count += 1
        print(f"Peer{origin.peer_id} originated message id=({origin.peer_id},{seq}).")

    start = asyncio.get_event_loop().time()
    origin_msg = (communities[0].peer_id, communities[0]._origin_seq) if communities else None
    delivered = False
    while True:
        if origin_msg and all(origin_msg in c.known_messages for c in communities):
            delivered = True
            break
        if asyncio.get_event_loop().time() - start >= duration:
            break
        await asyncio.sleep(1.0)

    # Stop all peers
    for svc in ipv8_services:
        await svc.stop()
    nodes = list(range(1, num_peers + 1))
    mid_to_id = {c.my_peer.mid: c.peer_id for c in communities}
    edges = set()
    for c in communities:
        for p in c.get_peers():
            pid = mid_to_id.get(p.mid)
            if pid and pid != c.peer_id:
                edges.add(tuple(sorted((c.peer_id, pid))))
    edges_list = [{'source': a, 'target': b} for a, b in sorted(edges)]
    topo = {'nodes': nodes, 'edges': edges_list}
    filename = f"topology_{topology}_{gossip_mode}.json"
    with open(filename, 'w') as f:
        json.dump(topo, f, indent=2)
    print(f"Topology JSON saved to {filename} (nodes={len(nodes)}, edges={len(edges_list)}).")
    total_sent = sum(c.sent_count for c in communities)
    total_dupes = sum(c.duplicate_count for c in communities)
    avg_sent = total_sent / num_peers if num_peers else 0
    print(f"Total messages sent: {total_sent}")
    print(f"Average per node: {avg_sent:.2f}")
    print(f"Duplicate receives: {total_dupes}")
    if delivered:
        print("Message delivered to all peers.")
    else:
        missing = [c.peer_id for c in communities if origin_msg not in c.known_messages]
        print(f"Message NOT delivered to peers: {missing}")

    # Clean up key files
    for i in range(1, num_peers + 1):
        try:
            os.remove(f"ec{i}.pem")
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("IPv8 Gossip Simulator")
    parser.add_argument("--nodes", type=int, default=100)
    parser.add_argument("--topology", choices=["sparse", "dense"], default="dense")
    parser.add_argument("--mode", choices=["push", "pull", "hybrid"], default="push")
    parser.add_argument("--duration", type=float, default=30.0)
    args = parser.parse_args()
    asyncio.run(start_communities(args.nodes, args.topology, args.mode, args.duration))