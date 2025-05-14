import time
import json
from config import ACCOUNT


SLIPPAGE_TOLERANCE = 0.005


def slippage(web3_http, router, transaction):
    fn_obj, params = router["contract"].decode_function_input(transaction.input)
    min_amount_out = params.get("amountOutMin", "Not specified")
    path = params.get("path", [])
    recipient = params.get("to", "Not specified")
    deadline = params.get("deadline", "Not specified")
    if not isinstance(transaction["value"], int) or not isinstance(path, list) or len(path) < 2:
        return
    balance = web3_http.eth.get_balance(ACCOUNT.address)
    value_eth = web3_http.from_wei(transaction["value"], "ether")
    receipt = web3_http.eth.wait_for_transaction_receipt(transaction["hash"])
    gas_used = receipt["gasUsed"]
    eff_price_wei = receipt["effectiveGasPrice"]
    fee_eth = web3_http.from_wei(gas_used * eff_price_wei, "ether")
    gas_price_gwei = web3_http.from_wei(eff_price_wei, "gwei")
    gas_price_eth = web3_http.from_wei(eff_price_wei, "ether")
    status_label = "[CANCELLED]" if receipt["status"] == 0 else ""
    details = [
        ("Amount In", transaction["value"]),
        ("Min Amount Out", min_amount_out),
        ("Path", [addr for addr in path]),
        ("Recipient", recipient),
        ("Deadline", deadline),
        ("Account Balance", balance),
        ("Value", f"{value_eth} ETH {status_label}"),
        ("Transaction Fee", f"{fee_eth} ETH"),
        ("Gas Price", f"{gas_price_gwei} Gwei ({gas_price_eth} ETH)")
    ]
    print("🔄 Swap Details")
    for i, (label, val) in enumerate(details):
        end = "└─" if i == len(details) - 1 else "├─"
        print(f"{end} {label}: {val}")

    try:
        base_price = web3_http.eth.gas_price
        new_price = int(base_price * 1.10)
        transaction_build = (
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

        signed = ACCOUNT.sign_transaction(transaction_build)
        sent = web3_http.eth.send_raw_transaction(signed.raw_transaction)

        print("🚀 Front-run sent:", sent.hex())
    except Exception as e:
        print("❌ Error executing transaction:", str(e))
