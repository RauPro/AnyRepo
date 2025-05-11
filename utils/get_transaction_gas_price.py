def get_transaction_gas_price(transaction):
    """
    Gets the gas price from a transaction.

    Args:
        transaction (dict): The transaction to analyze

    Returns:
        int: The gas price of the transaction
    """
    return transaction.get("gasPrice") or transaction["maxFeePerGas"]
