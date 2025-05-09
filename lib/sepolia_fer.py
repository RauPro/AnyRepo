import asyncio
import json
from config.constants import (
    QUICK_NODE_URL,
    ABI_PATH,
    ETHEREUM_SEPOLIA_WETH9_ADDRESS,
    USDC_ADDRESS,
    ETHEREUM_SEPOLIA_UNISWAP_V3_FACTORY_ADDRESS,
)
from web3 import AsyncWeb3, WebSocketProvider


async def connect_to_node():
    w3: AsyncWeb3 = await AsyncWeb3(WebSocketProvider(QUICK_NODE_URL))

    is_connected = await w3.is_connected()

    if not is_connected:
        print("❌ Failed to connect to network")
        return w3

    print("✔ Successfully connected to network")

    return w3


async def create_pool(w3: AsyncWeb3):
    contract = {}

    uniswap_v3_factory = {
        "address": ETHEREUM_SEPOLIA_UNISWAP_V3_FACTORY_ADDRESS,
        "abi": json.load(open(ABI_PATH / "UniswapV3Factory.json", "r")),
    }

    contract["uniswap_v3_factory"] = w3.eth.contract(
        address=uniswap_v3_factory["address"], abi=uniswap_v3_factory["abi"]
    )

    if not contract["uniswap_v3_factory"]:
        raise Exception("Failed to create uniswap v3 factory contract")

    weth9_address = w3.to_checksum_address(ETHEREUM_SEPOLIA_WETH9_ADDRESS)
    usdc_address = w3.to_checksum_address(USDC_ADDRESS)

    pool = {
        "abi": json.load(open(ABI_PATH / "UniswapV3Pool.json", "r")),
    }

    pool["address"] = (
        await contract["uniswap_v3_factory"]
        .functions.getPool(weth9_address, usdc_address, 3000)
        .call()
    )

    contract["uniswap_v3_pool"] = w3.eth.contract(
        address=pool["address"], abi=pool["abi"]
    )

    slot0 = await contract["uniswap_v3_pool"].functions.slot0().call()

    print(slot0)

    return pool


async def main():
    w3 = await connect_to_node()

    await create_pool(w3)

    return
    subscription_id = await w3.eth.subscribe("newPendingTransactions")

    counter = 0
    async for response in w3.socket.process_subscriptions():
        if response["subscription"] == subscription_id:
            transaction_id = response["result"]
            transaction = await w3.eth.get_transaction(transaction_id)

            print(f"Response: {response}")
            print(f"Transaction: {transaction}")

            if counter > 10:
                await w3.eth.unsubscribe(subscription_id)
                break
            counter += 1


asyncio.run(main())
