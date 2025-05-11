from config import ROUTER_CHECKSUM_ADDRESS
from data.constants import SWAP_SELECTORS


def is_uniswap_router_transaction(transaction):
    """
    Analyzes if a transaction is a Uniswap router swap transaction.

    Args:
        transaction (dict): The transaction to analyze

    Returns:
        bool: True if the transaction is a Uniswap router swap
    """
    return (
        transaction
        and transaction.get("to")
        and transaction["to"].lower() == ROUTER_CHECKSUM_ADDRESS.lower()
        and transaction["input"][:4] in SWAP_SELECTORS
    )
