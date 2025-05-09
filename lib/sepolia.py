import os
import asyncio
import json
from dotenv import load_dotenv
from eth_utils import to_hex

from web3 import AsyncWeb3, WebSocketProvider

load_dotenv()

QUICK_NODE_API_KEY = os.getenv("QUICK_NODE_API_KEY")

wss_url = (
    f"wss://skilled-little-gadget.ethereum-sepolia.quiknode.pro/{QUICK_NODE_API_KEY}"
)


ROUTERS = {
    # Uniswap V2
    "0xee567fe1712faf6149d80da1e6934e354124cfe3",
    # Uniswap V3
    "0xe592427a0aece92de3edee1f18e0157c05861564",
    "0x3bfa4769fb09eefc5a80d6e87c3b9c650f7ae48e",
    # Universal Router
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad",
}

SWAP_SELECTORS = {
    # — V2 —
    b"\x7f\xf3j\xb5", b"\xfb=\xdbA", b"\x18\xcb\xaf\xe5",
    b"J%\xd9J",       b"8\xed\x17\x39", b"\x88\x03\xdb\xee",
    # — V3 —
    b"\x04\xe4Z\xaf",   # exactInputSingle
    b"P#\xb4\xdf",      # exactInput
    b"\xdb>!\x98",      # exactOutputSingle
    b"\t\xb8\x13F",     # exactOutput
    # — Universal Router —
    b"5\x93VL",         # execute / multicall
}

def is_swap(tx):
    """True ⇢ tx is a call to a router & its 4-byte selector matches a swap fn."""
    if tx["to"] is None or tx["input"] == b"":
        return False
    return tx["to"].lower() in ROUTERS and tx["input"][:4] in SWAP_SELECTORS

def gas_price(tx):
    """Unify legacy & EIP-1559."""
    return tx.get("gasPrice") or tx["maxFeePerGas"]

async def main():
    async with AsyncWeb3(WebSocketProvider(wss_url)) as w3:
        print("is_connected:", await w3.is_connected())

        sub_id   = await w3.eth.subscribe("newPendingTransactions")
        raw_txs  = []                      
        counter  = 0

        async for msg in w3.socket.process_subscriptions():
            tx_hash = msg["result"]
            tx      = await w3.eth.get_transaction(tx_hash)
            raw_txs.append(tx)              

            counter += 1
            if counter > 50:                
                await w3.eth.unsubscribe(sub_id)
                break

        swap_txs = [tx for tx in raw_txs if is_swap(tx)]

        swap_txs.sort(key=gas_price, reverse=True)

        print(f"\nKept {len(swap_txs)} swap transactions")
        for tx in swap_txs[:10]:       
            print(to_hex(tx['hash']), "gas", gas_price(tx))


        with open("swaps.json", "w") as f:
            json.dump([dict(tx) for tx in swap_txs],
                      f, indent=2, default=to_hex)

asyncio.run(main())