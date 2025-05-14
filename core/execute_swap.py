import json
import os
import random
import time
from config import ACCOUNT, CHAIN_ID
from eth_utils import to_hex



def execute_swap(web3, router):
    """
    Executes a test swap transaction on the Uniswap router.

    Args:
        web3: Web3 instance
        router_contract: Contract instance of the Uniswap router

    Returns:
        str: Transaction hash of the executed swap
    """
    if random.random() < 0.9:
        amount_eth = round(random.uniform(0.0003, 0.002), 6)
    else:
        amount_eth = round(random.uniform(0.005, 0.02), 6)

    deadline = int(time.time()) + 900
    nonce = web3.eth.get_transaction_count(ACCOUNT.address, "pending")
    weth_address = router["contract"].functions.WETH().call()
    usdc_address = os.getenv("USDC_TOKEN")
    #get_liquidity(web3, weth_address, usdc_address)
    tx = (
        router["contract"]
        .functions.swapExactETHForTokens(
            0, [router["address"], router["address"]], ACCOUNT.address, deadline
        )
        .build_transaction(
            {
                "from": ACCOUNT.address,
                "value": web3.to_wei(amount_eth, "ether"),
                "nonce": nonce,
                "gas": 250_000,
                "maxFeePerGas": web3.to_wei(30, "gwei"),
                "maxPriorityFeePerGas": web3.to_wei(2, "gwei"),
                "chainId": CHAIN_ID,
            }
        )
    )
    signed = ACCOUNT.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    print("💸 Sent test swap:", to_hex(tx_hash))
    return tx_hash