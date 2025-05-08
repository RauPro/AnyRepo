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
    v2_factory_abi = json.load(open("IUniswapV3Factory.json", 'r'))
    # print(v2_factory_abi["abi"])
    UNISWAP_V3_FACTORY = "0x0227628f3F023bb0B980b67D528571c95c6DaC1c"
    factory = w3.eth.contract(address=UNISWAP_V3_FACTORY, abi=v2_factory_abi["abi"])
    TOKEN_A = w3.to_checksum_address("0xfff9976782d46cc05630d1f6ebab18b2324d6b14") # WETH
    TOKEN_B = w3.to_checksum_address("0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8") # USDC
    pair_addr = await factory.functions.getPool(TOKEN_B, TOKEN_A, 3000).call()
    print(pair_addr)
    if int(pair_addr, 16) == 0:
        print("❌ No UniswapV3 pool exists for this token pair → no liquidity.")
        return
    print(f"🔗 Pair contract: {pair_addr}")
    v3_pool_state_abi = json.load(open("./IUniswapV3PoolState.json", 'r'))
    pool_state_contract = w3.eth.contract(address=pair_addr, abi=v3_pool_state_abi["abi"])
    state = await pool_state_contract.functions.slot0().call()
    #print(f"Reserves: token0={reserve0}, token1={reserve1}")
    print(state)
    if state:
        print("✅ Pool has liquidity!", state[0])
    else:
        print("⚠️ Pool exists but reserves are zero → effectively no liquidity.")
asyncio.run(main())