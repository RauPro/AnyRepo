import asyncio
import json
import random
import sys
import time

from prettytable import PrettyTable
from core import execute_swap
from eth_utils import to_hex
from services import (
    establish_quicknode_http_connection,
    establish_quicknode_websocket_connection,
    initialize_uniswap_router,
)
from utils import get_transaction_gas_price, is_uniswap_router_transaction

web3_http = establish_quicknode_http_connection()
router = initialize_uniswap_router(web3_http)


async def collect_router_swaps(max_swaps=20, max_seconds=60, ready_flag=None):
    swaps, start = [], time.time()
    async with await establish_quicknode_websocket_connection() as aw3:
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
                    f"👁️ Swap seen: {to_hex(tx_hash)} gas {get_transaction_gas_price(tx)}"
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
        execute_swap(web3_http, router)
        await asyncio.sleep(0.5)

    swaps = await listener

    print(
        f"\n🎯 Successfully captured {len(swaps)} router {'swap' if len(swaps) == 1 else 'swaps'}! 🚀"
    )

    swaps.sort(key=get_transaction_gas_price, reverse=True)

    t = PrettyTable(["Transaction Hash", "Gas Price"])
    t.hrules = True
    for tx in swaps:
        t.add_row([to_hex(tx["hash"]), get_transaction_gas_price(tx)])
    print(t)

    with open("output/swaps.json", "w") as f:
        json.dump([dict(tx) for tx in swaps], f, indent=2, default=to_hex)


if __name__ == "__main__":
    asyncio.run(main())
