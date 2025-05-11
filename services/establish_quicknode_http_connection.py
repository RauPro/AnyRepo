from config import (
    QUICK_NODE_HTTP_URL,
)
from web3 import Web3, HTTPProvider


def establish_quicknode_http_connection():
    """
    Establishes an HTTP connection to the QuickNode endpoint.

    Returns:
        Web3: The Web3 instance connected to QuickNode HTTP endpoint.
        If connection fails, returns the Web3 instance anyway but prints error message.
    """
    web3_http = Web3(HTTPProvider(QUICK_NODE_HTTP_URL))

    is_connected = web3_http.is_connected()

    if not is_connected:
        print("❌ Failed to connect to QuickNode HTTP endpoint at", QUICK_NODE_HTTP_URL)
        return web3_http

    print("✔ Successfully connected to QuickNode HTTP endpoint at", QUICK_NODE_HTTP_URL)

    return web3_http
