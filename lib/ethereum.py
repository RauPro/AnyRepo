import os
import asyncio
from dotenv import load_dotenv

from web3 import AsyncWeb3
from web3.providers.persistent import (
    WebSocketProvider,
)

load_dotenv()

INFURA_API_KEY = os.getenv("INFURA_API_KEY")

wss_url = f"wss://mainnet.infura.io/ws/v3/{INFURA_API_KEY}"


async def subscribe_pending_transactions():
    async with AsyncWeb3(WebSocketProvider(wss_url)) as w3:
        subscription = await w3.eth.subscribe("newHeads")
        async for tx_hash in subscription:
            print(f"Pending transaction hash: {tx_hash}")
            # If you want transaction details:
            tx = await w3.eth.get_transaction(tx_hash)
            print(tx)


asyncio.run(subscribe_pending_transactions())
