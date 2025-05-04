import asyncio
from ipv8.configuration import ConfigBuilder, WalkerDefinition, Strategy, default_bootstrap_defs
from ipv8_service import IPv8
from communities import TokenCommunity

async def main():
    roles = ["miner", "sniper", "user", "whale"]
    builders = []
    for i, role in enumerate(roles, start=1):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "medium", f"keys/ec{i}.pem")
        builder.add_overlay("TokenCommunity", "my peer",
                            [WalkerDefinition(Strategy.RandomWalk, 10, {'timeout': 3.0})],
                            default_bootstrap_defs,
                            {"role": role}, [('started',)])
        builders.append(builder)
    ipv8_instances = []
    for builder in builders:
        ipv8 = await IPv8(builder.finalize(), extra_communities={"TokenCommunity": TokenCommunity}).start()
        ipv8_instances.append(ipv8)
    await asyncio.Future()
asyncio.run(main())
