import time
import json
from config import ACCOUNT


SLIPPAGE_TOLERANCE = 0.005


def slippage(web3_http, router, transaction):
    fn_obj, params = router["contract"].decode_function_input(transaction.input)

    path = params.get("path", [])
    token_address = path[0]

    print("🔍 Token address:", token_address)
    if token_address != "0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3":
        print("🟡 Not interested in this token because it's not WETH")
        return

    value = transaction.value

    if not isinstance(value, int) or not isinstance(path, list) or len(path) < 2:
        print("🟡️ Not interested in this token because transaction format is invalid")
        return

    print("📝 Transaction:")
    for key, value in transaction.items():
        print(f"├─ {key}: {value}")
    print("└─")

    print("📝 Transaction input:")
    for key, value in params.items():
        print(f"├─ {key}: {value}")
    print("└─")

    token_contract = web3_http.eth.contract(
        address=token_address, abi=json.load(open("abi/UniswapV2ERC20.json", "r"))
    )

    amounts = router["contract"].functions.getAmountsOut(value, path).call()

    expected_out = amounts[-1]

    min_out = int(expected_out * (1 - SLIPPAGE_TOLERANCE))

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
