import asyncio
import json
import os
import random
import sys
import time
from dotenv import load_dotenv
from eth_account import Account
from eth_utils import to_hex
from web3 import AsyncWeb3, HTTPProvider, Web3, WebSocketProvider

load_dotenv()

ACCOUNT_PRIVATE_KEY = os.getenv("ACCOUNT_PRIVATE_KEY")

if not (ACCOUNT_PRIVATE_KEY):
    sys.exit("🔑 Please add your private key to the .env file to continue!")

QUICK_NODE_HTTP_URL = os.getenv("QUICK_NODE_HTTP_URL")

if not (QUICK_NODE_HTTP_URL):
    sys.exit("🔑 Please add your quick node http url to the .env file to continue!")

QUICK_NODE_WSS_URL = os.getenv("QUICK_NODE_WSS_URL")

if not (QUICK_NODE_WSS_URL):
    sys.exit("🔑 Please add your quick node wss url to the .env file to continue!")

CHAIN_ID_NUMBER = os.getenv("CHAIN_ID_NUMBER")

if not (CHAIN_ID_NUMBER):
    sys.exit("🔑 Please add your chain id to the .env file to continue!")

CHAIN_ID = int(CHAIN_ID_NUMBER)

ROUTER_ADDRESS = os.getenv("ROUTER_ADDRESS")

if not (ROUTER_ADDRESS):
    sys.exit("🔑 Please add your router address to the .env file to continue!")

ROUTER = Web3.to_checksum_address(ROUTER_ADDRESS)

SWAP_SEL = {  # V2/V3/UR selectors
    b"\x7f\xf3j\xb5",
    b"\xfb=\xdbA",
    b"\x18\xcb\xaf\xe5",
    b"J%\xd9J",
    b"8\xed\x17\x39",
    b"\x88\x03\xdb\xee",
    b"\x04\xe4Z\xaf",
    b"P#\xb4\xdf",
    b"\xdb>!\x98",
    b"\t\xb8\x13F",
    b"5\x93VL",
}


def is_router_swap(tx):
    return (
        tx
        and tx.get("to")
        and tx["to"].lower() == ROUTER.lower()
        and tx["input"][:4] in SWAP_SEL
    )


def gas_price(tx):
    return tx.get("gasPrice") or tx["maxFeePerGas"]


w3 = Web3(HTTPProvider(QUICK_NODE_HTTP_URL))
acct = Account.from_key(ACCOUNT_PRIVATE_KEY)
with open("IUniswapV2Router02.json") as f:
    router_abi = json.load(f)["abi"]
router = w3.eth.contract(address=ROUTER, abi=router_abi)


def fire_test_swap():
    if random.random() < 0.9:
        amount_eth = round(random.uniform(0.0003, 0.002), 6)
        fee_gwei = 30
    else:
        amount_eth = round(random.uniform(0.005, 0.02), 6)
        fee_gwei = 40

    deadline = int(time.time()) + 900
    nonce = w3.eth.get_transaction_count(acct.address, "pending")

    tx = router.functions.swapExactETHForTokens(
        0, [router.address, router.address], acct.address, deadline
    ).build_transaction(
        {
            "from": acct.address,
            "value": w3.to_wei(amount_eth, "ether"),
            "nonce": nonce,
            "gas": 250_000,
            "maxFeePerGas": w3.to_wei(30, "gwei"),
            "maxPriorityFeePerGas": w3.to_wei(2, "gwei"),
            "chainId": CHAIN_ID,
        }
    )
    signed = acct.sign_transaction(tx)
    h = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("⟶ sent test swap", to_hex(h))


ready = asyncio.Event()


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
            if tx and is_router_swap(tx):
                swaps.append(tx)
                print(f"✓ swap seen {to_hex(tx_hash)} gas {gas_price(tx)}")
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
    swaps.sort(key=gas_price, reverse=True)
    for tx in swaps:
        print(to_hex(tx["hash"]), "gas", gas_price(tx))

    with open("swaps.json", "w") as f:
        json.dump([dict(tx) for tx in swaps], f, indent=2, default=to_hex)


if __name__ == "__main__":
    asyncio.run(main())
