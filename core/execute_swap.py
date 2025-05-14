import json
import os
import random
import time
from config import ACCOUNT, CHAIN_ID
from eth_utils import to_hex



def execute_swap(web3, router, amount_eth):
    """
    Executes a test swap transaction on the Uniswap router.

    Args:
        web3: Web3 instance
        router_contract: Contract instance of the Uniswap router

    Returns:
        str: Transaction hash of the executed swap
    """

    deadline = int(time.time()) + 900
    nonce = web3.eth.get_transaction_count(ACCOUNT.address, "pending")
    weth_address = web3.to_checksum_address(os.getenv("WETH_TOKEN"))
    usdc_address = web3.to_checksum_address(os.getenv("USDC_TOKEN"))
    #get_liquidity(web3, weth_address, usdc_address)
    amount_in_wei = web3.to_wei(amount_eth, "ether")
    print(web3.to_wei(amount_eth * 1.1, "ether"))
    amounts_out = router["contract"].functions.getAmountsOut(
        amount_in_wei,
        [usdc_address, weth_address]
    ).call()
    min_amount_out = int(amounts_out[-1] * (1 - 0.01))

    tx = (
        router["contract"]
        .functions.swapExactETHForTokens(
            min_amount_out, [router["address"], router["address"]], ACCOUNT.address, deadline
        )
        .build_transaction(
            {
                "from": ACCOUNT.address,
                "value": amount_in_wei,
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