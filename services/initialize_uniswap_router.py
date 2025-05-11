import json
from config import ROUTER_CHECKSUM_ADDRESS
from web3 import Web3


def initialize_uniswap_router(web3_instance: Web3):
    """
    Initializes the Uniswap V2 Router contract.

    Returns:
        dict: The router configuration containing address, abi, and contract instance.
        If initialization fails, returns the router dict anyway but prints error message.
    """
    router = {
        "address": ROUTER_CHECKSUM_ADDRESS,
        "abi": json.load(open("abi/UniswapV2Router02.json", "r")),
        "contract": None,
    }

    try:
        router["contract"] = web3_instance.eth.contract(
            address=ROUTER_CHECKSUM_ADDRESS, abi=router["abi"]
        )
        print(
            "✔ Successfully initialized Uniswap V2 Router contract at",
            ROUTER_CHECKSUM_ADDRESS,
        )
    except Exception as e:
        print("❌ Failed to initialize Uniswap V2 Router contract:", str(e))

    return router
