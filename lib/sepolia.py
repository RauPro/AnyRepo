import os, json, time, asyncio
from dotenv import load_dotenv
from eth_account import Account
from eth_utils import to_hex
from web3 import Web3, AsyncWeb3, WebSocketProvider

try:                          
    from web3.providers.http import HTTPProvider
except ImportError:                    
    from web3 import HTTPProvider

load_dotenv()
API_KEY = os.getenv("QUICK_NODE_API_KEY")
PK      = os.getenv("PRIVATE_KEY")
if not (API_KEY and PK):
    raise SystemExit("Set QUICK_NODE_API_KEY and PRIVATE_KEY in .env")

HTTP_URL = f"https://skilled-little-gadget.ethereum-sepolia.quiknode.pro/{API_KEY}"
WSS_URL  = f"wss://skilled-little-gadget.ethereum-sepolia.quiknode.pro/{API_KEY}"

ROUTER  = Web3.to_checksum_address("0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3")
WETH    = Web3.to_checksum_address("0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14")
DAI     = Web3.to_checksum_address("0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6")
CHAINID = 11155111

SWAP_SEL = {
    b"\x7f\xf3j\xb5", b"\xfb=\xdbA", b"\x18\xcb\xaf\xe5",
    b"J%\xd9J",       b"8\xed\x17\x39", b"\x88\x03\xdb\xee",
    b"\x04\xe4Z\xaf", b"P#\xb4\xdf",   b"\xdb>!\x98", b"\t\xb8\x13F",
    b"5\x93VL",
}

def is_swap(tx):
    return (
        tx["to"]
        and tx["to"].lower() == ROUTER.lower()
        and tx["input"][:4] in SWAP_SEL
    )

def gas_price(tx):
    return tx.get("gasPrice") or tx["maxFeePerGas"]

w3 = Web3(HTTPProvider(HTTP_URL))

acct = Account.from_key(PK)
with open("IUniswapV2Router02.json") as f:
    artifact = json.load(f)

router_abi = artifact["abi"]        
router = w3.eth.contract(address=ROUTER, abi=router_abi)

def send_demo_swap(amount_eth=0.001):
    deadline = int(time.time()) + 600

    nonce = w3.eth.get_transaction_count(acct.address, 'pending')

    tx = router.functions.swapExactETHForTokens(
        0, [WETH, DAI], acct.address, deadline
    ).build_transaction({
        "from":  acct.address,
        "value": w3.to_wei(amount_eth, "ether"),
        "nonce": nonce,            
        "gas":   250_000,
        "maxFeePerGas": w3.to_wei(30, "gwei"),
        "maxPriorityFeePerGas": w3.to_wei(2, "gwei"),
        "chainId": CHAINID,
    })
    raw = acct.sign_transaction(tx).raw_transaction
    h   = w3.eth.send_raw_transaction(raw)
    print("↳ demo swap sent:", to_hex(h))
    return h

async def listen_and_collect(max_raw=50):
    async with AsyncWeb3(WebSocketProvider(WSS_URL)) as aw3:
        print("WS connected ↔", await aw3.is_connected())
        sub_id = await aw3.eth.subscribe("newPendingTransactions")
        raw_pool = []

        async for msg in aw3.socket.process_subscriptions():
            tx_hash = msg["result"]
            tx = await aw3.eth.get_transaction(tx_hash)
            raw_pool.append(tx)

            if len(raw_pool) >= max_raw:
                await aw3.eth.unsubscribe(sub_id)
                break

    swaps = [tx for tx in raw_pool if is_swap(tx)]
    swaps.sort(key=gas_price, reverse=True)
    return swaps

async def main():
    for _ in range(2):
        send_demo_swap(0.001)
        await asyncio.sleep(3)

    swaps = await listen_and_collect(50)

    print(f"\nKept {len(swaps)} swap transactions")
    for tx in swaps[:10]:
        print(to_hex(tx["hash"]), "gas", gas_price(tx))

    with open("swaps.json", "w") as f:
        json.dump([dict(tx) for tx in swaps], f, indent=2, default=to_hex)

if __name__ == "__main__":
    asyncio.run(main())
