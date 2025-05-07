import asyncio
import json
import os
from eth_account import Account
from web3.auto import w3
from dotenv import load_dotenv
from web3 import AsyncWeb3, WebSocketProvider
from utils.utils import load_latest_keystore


load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
acct = Account.from_key(PRIVATE_KEY)


RPC_WS_URL = os.getenv("QUICK_NODE_API_URL")
wss_url = (RPC_WS_URL)
CHAIN_ID = 11155111


async def main():
    w3 = await AsyncWeb3(WebSocketProvider(RPC_WS_URL))
    chain_id = await w3.eth.chain_id
    if chain_id != CHAIN_ID:
        print(f"Connected to wrong network (Chain ID {chain_id}). Check RPC URL.")
        return
    print(f"✔ Connected to Sepolia (Chain ID {chain_id})")

    account = w3.eth.account.from_key(PRIVATE_KEY)
    bot_address = account.address
    print(f"✔ Bot address loaded: {bot_address}")
    print(f"Current Sepolia block: {await w3.eth.block_number}")
    balance = await w3.eth.get_balance(bot_address)
    print(f"Bot ETH balance: {w3.from_wei(balance, 'ether')} ETH")


v2_factory_abi = json.load(open("./IUniswapV2Router02.json", 'r'))
# print(v2_factory_abi["abi"])
UNISWAP_V2_ROUTER = "0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3"
router_v2_abi = [...]
router = w3.eth.contract(address=UNISWAP_V2_ROUTER, abi=v2_factory_abi["abi"])

asyncio.run(main())
