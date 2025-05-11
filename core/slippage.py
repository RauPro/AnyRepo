import time
import json
from config import ACCOUNT


SLIPPAGE_TOLERANCE = 0.005


def slippage(web3_http, router, transaction):
    fn_obj, params = router["contract"].decode_function_input(transaction.input)

    amount_in = params.get("amountIn", "Not specified")
    min_amount_out = params.get("amountOutMin", "Not specified")
    path = params.get("path", [])
    recipient = params.get("to", "Not specified")
    deadline = params.get("deadline", "Not specified")

    print("🔄 Swap Details")
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
    print(f"🪙  Token Contract Address: {token_in_address}")

    balance = token_contract.functions.balanceOf(ACCOUNT.address).call()

    print(f"🏦 Balance: {balance}")

    allowance = token_contract.functions.allowance(
        ACCOUNT.address, router["address"]
    ).call()

    print(f"💎 Allowance: {allowance}")

    print("💰 Amounts")
    print(f"├─ Balance: {web3_http.from_wei(balance, 'ether')} ETH")
    print("├─ Expected Out:", expected_out)
    print("└─ Min Out:", min_out)

    try:
        assert balance >= amount_in
        assert allowance >= amount_in

        base_price = web3_http.eth.gas_price
        new_price = int(base_price * 1.10)

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
        print("❌ Error executing transaction:", str(e))
