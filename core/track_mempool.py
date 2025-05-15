import asyncio
import time
from eth_utils import to_hex
from services import establish_quicknode_websocket_connection
from utils import get_transaction_gas_price, is_uniswap_router_transaction
from core.slippage import slippage_trigger


async def track_mempool(
    max_swaps=20, max_seconds=60, subscription_ready=None, router=None, web3_http=None
):
    """
    Tracks the Ethereum mempool for Uniswap router transactions.

    Establishes a WebSocket connection to monitor pending transactions, filters for
    Uniswap router transactions, and collects them until either the maximum number
    of swaps is reached or the timeout period elapses.

    Args:
        max_swaps (int, optional): Maximum number of swap transactions to collect. Defaults to 20.
        max_seconds (int, optional): Maximum time in seconds to monitor mempool. Defaults to 60.
        subscription_ready (asyncio.Event, optional): Event to signal when subscription is ready.
            Used for synchronization with other tasks. Defaults to None.

    Returns:
        list: List of collected Uniswap swap transactions, where each transaction is a dict
        containing transaction details like hash, gas price, etc.
    """
    swaps, start = [], time.time()
    async with await establish_quicknode_websocket_connection() as web3_wss:
        sub_id = await web3_wss.eth.subscribe("newPendingTransactions")

        if subscription_ready:
            subscription_ready.set()

        start = time.time()

        async for pending_transaction in web3_wss.socket.process_subscriptions():
            transaction_hash = pending_transaction["result"]

            try:
                transaction = await web3_wss.eth.get_transaction(transaction_hash)
            except Exception:
                continue

            if transaction is None:
                await asyncio.sleep(0.3)
                try:
                    transaction = await web3_wss.eth.get_transaction(transaction_hash)
                except Exception:
                    continue
            if transaction and is_uniswap_router_transaction(transaction):
                slippage_trigger(web3_http, router, transaction)
                swaps.append(transaction)

                print(
                    f"👁️  Swap seen: {to_hex(transaction_hash)} with gas price {get_transaction_gas_price(transaction)}"
                )

                if len(swaps) >= max_swaps:
                    break

            elapsed_time = time.time() - start
            if elapsed_time > max_seconds:
                print("⏰ Timeout reached")
                break

        await web3_wss.eth.unsubscribe(sub_id)
    return swaps
