import asyncio
import time
import json
from eth_utils import to_hex
from services import establish_quicknode_websocket_connection
from utils import get_transaction_gas_price, is_uniswap_router_transaction
from eth_abi import decode
from config import ACCOUNT


SLIPPAGE_TOLERANCE = 0.005


def slippage(web3_http, router, transaction):

    base_price = web3_http.eth.gas_price
    new_price = int(base_price * 1.10)

    fn_obj, params = router["contract"].decode_function_input(transaction.input)

    amount_in = params.get("amountIn", "Not specified")
    min_amount_out = params.get("amountOutMin", "Not specified")
    path = params.get("path", [])
    recipient = params.get("to", "Not specified")
    deadline = params.get("deadline", "Not specified")

    print("\n🔄 Swap Details")
    print("├─ Amount In:", amount_in)
    print("├─ Min Amount Out:", min_amount_out)
    print("├─ Path:", [addr for addr in path])
    print("├─ Recipient:", recipient)
    print("└─ Deadline:", deadline)

    # only continue if amount_in is a number and path is a list
    if not isinstance(amount_in, int) or not isinstance(path, list) or len(path) < 2:
        return

    amounts = router["contract"].functions.getAmountsOut(amount_in, path).call()
    expected_out = amounts[-1]
    min_out = int(expected_out * (1 - SLIPPAGE_TOLERANCE))

    token_in_address = path[0]

    token_contract = web3_http.eth.contract(
        address=token_in_address, abi=json.load(open("abi/UniswapV2ERC20.json", "r"))
    )
    # print contract address
    print(f"🪙 Token Contract Address: {token_in_address}")

    balance = token_contract.functions.balanceOf(ACCOUNT.address).call()

    print(f"\n🏦 Balance: {balance}")

    allowance = token_contract.functions.allowance(
        ACCOUNT.address, router["address"]
    ).call()

    print(f"\n💎 Allowance: {allowance}")

    print("\n💰 Amounts")
    print(f"├─ Balance: {web3_http.from_wei(balance, 'ether')} ETH")
    print("├─ Expected Out:", expected_out)
    print("└─ Min Out:", min_out)

    try:
        assert balance >= amount_in
        assert allowance >= amount_in
        tx_build = (
            router["contract"]
            .functions.swapExactTokensForTokens(
                amount_in, min_out, path, ACCOUNT.address, int(time.time()) + 60
            )
            .build_transaction(
                {
                    "from": ACCOUNT.address,
                    "gas": 300_000,
                    "gasPrice": new_price,
                    "nonce": web3_http.eth.get_transaction_count(
                        ACCOUNT.address, block_identifier="pending"
                    ),
                }
            )
        )

        signed = ACCOUNT.sign_transaction(tx_build)
        sent = web3_http.eth.send_raw_transaction(signed.raw_transaction)

        print("🚀 Front-run sent:", sent.hex())
    except Exception as e:
        print("❌ Error executing front-run transaction:", str(e))


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
                slippage(web3_http, router, transaction)

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
