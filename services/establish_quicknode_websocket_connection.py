from config import (
    QUICK_NODE_WSS_URL,
)
from web3 import AsyncWeb3, WebSocketProvider


async def establish_quicknode_websocket_connection():
    """
    Establishes a WebSocket connection to the QuickNode endpoint.

    Returns:
        AsyncWeb3: The AsyncWeb3 instance connected to QuickNode WebSocket endpoint.
        If connection fails, returns the AsyncWeb3 instance anyway but prints error message.
    """
    web3_wss: AsyncWeb3 = await AsyncWeb3(WebSocketProvider(QUICK_NODE_WSS_URL))

    is_connected = await web3_wss.is_connected()

    if not is_connected:
        print("❌ Failed to connect to QuickNode WSS endpoint at", QUICK_NODE_WSS_URL)
        return web3_wss

    print("✅ Successfully connected to QuickNode WSS endpoint at", QUICK_NODE_WSS_URL)

    return web3_wss
