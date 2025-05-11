import asyncio
import json
import random
import time
import sys
from config import (
    ACCOUNT,
    CHAIN_ID,
    QUICK_NODE_HTTP_URL,
    QUICK_NODE_WSS_URL,
    ROUTER_CHECKSUM_ADDRESS,
)
from eth_utils import to_hex
from web3 import AsyncWeb3, HTTPProvider, Web3, WebSocketProvider

from utils import is_uniswap_router_transaction, get_transaction_gas_price


def connect_to_quicknode_http():
    """
    Establishes an HTTP connection to the QuickNode endpoint.

    Returns:
        Web3: The Web3 instance connected to QuickNode HTTP endpoint.
        If connection fails, returns the Web3 instance anyway but prints error message.
    """
    w3 = Web3(HTTPProvider(QUICK_NODE_HTTP_URL))

    is_connected = w3.is_connected()

    if not is_connected:
        print("❌ Failed to connect to QuickNode HTTP endpoint at", QUICK_NODE_HTTP_URL)
        return w3

    print("✔ Successfully connected to QuickNode HTTP endpoint at", QUICK_NODE_HTTP_URL)

    return w3


w3 = connect_to_quicknode_http()

with open("abi/UniswapV2Router02.json") as f:
    router_abi = json.load(f)

router = w3.eth.contract(address=ROUTER_CHECKSUM_ADDRESS, abi=router_abi)

print(router)


def fire_test_swap():
    if random.random() < 0.9:
        amount_eth = round(random.uniform(0.0003, 0.002), 6)
        fee_gwei = 30
    else:
        amount_eth = round(random.uniform(0.005, 0.02), 6)
        fee_gwei = 40

    deadline = int(time.time()) + 900
    nonce = w3.eth.get_transaction_count(ACCOUNT.address, "pending")

    tx = router.functions.swapExactETHForTokens(
        0, [router.address, router.address], ACCOUNT.address, deadline
    ).build_transaction(
        {
            "from": ACCOUNT.address,
            "value": w3.to_wei(amount_eth, "ether"),
            "nonce": nonce,
            "gas": 250_000,
            "maxFeePerGas": w3.to_wei(30, "gwei"),
            "maxPriorityFeePerGas": w3.to_wei(2, "gwei"),
            "chainId": CHAIN_ID,
        }
    )
    signed = ACCOUNT.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("⟶ sent test swap", to_hex(h))


async def collect_router_swaps(max_swaps=20, max_seconds=60, ready_flag=None):
    swaps, start = [], time.time()
    async with AsyncWeb3(WebSocketProvider(QUICK_NODE_WSS_URL)) as aw3:
        sub_id = await aw3.eth.subscribe("newPendingTransactions")
        if ready_flag:
            ready_flag.set()
        start = time.time()

        async for msg in aw3.socket.process_subscriptions():
            tx_hash = msg["result"]
            try:
                tx = await aw3.eth.get_transaction(tx_hash)
            except Exception:
                continue

            if tx is None:
                await asyncio.sleep(0.3)
                try:
                    tx = await aw3.eth.get_transaction(tx_hash)
                except Exception:
                    continue
            if tx and is_uniswap_router_transaction(tx):
                swaps.append(tx)
                print(
                    f"✓ swap seen {to_hex(tx_hash)} gas {get_transaction_gas_price(tx)}"
                )
                if len(swaps) >= max_swaps:
                    break

            if time.time() - start > max_seconds:
                print("⏰ hit timeout")
                break

        await aw3.eth.unsubscribe(sub_id)
    return swaps


async def main():
    ready = asyncio.Event()
    listener = asyncio.create_task(
        collect_router_swaps(max_swaps=20, max_seconds=60, ready_flag=ready)
    )

    await ready.wait()

    for _ in range(3):
        fire_test_swap()
        await asyncio.sleep(0.5)

    swaps = await listener

    print(f"\nCaptured {len(swaps)} router swaps")
    swaps.sort(key=get_transaction_gas_price, reverse=True)
    for tx in swaps:
        print(to_hex(tx["hash"]), "gas", get_transaction_gas_price(tx))

    with open("swaps.json", "w") as f:
        json.dump([dict(tx) for tx in swaps], f, indent=2, default=to_hex)


if __name__ == "__main__":
    asyncio.run(main())
