import os
import time
import json
from config import ACCOUNT
from services.get_liquidity_weth_usdc import get_liquidity_and_price, simulate_swap, max_input_for_slippage, \
    simulate_front_run_profit

SLIPPAGE_TOLERANCE = 0.005
weth_decimals = 18

def slippage_trigger(web3_http, router, transaction):
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
    fee_pct_value = (float(fee_eth) / float(value_eth) * 100) if value_eth > 0 else 0
    details = [
        ("Amount In", transaction["value"]),
        ("Min Amount Out", min_amount_out),
        ("Path", [addr for addr in path]),
        ("Recipient", recipient),
        ("Deadline", deadline),
        ("Account Balance", balance),
        ("Value", f"{value_eth} ETH {status_label}"),
        ("Transaction Fee", f"{fee_eth} ETH"),
        ("Gas Price", f"{gas_price_gwei} Gwei ({gas_price_eth} ETH)"),
        ("Fee % of value", f"{fee_pct_value:.4f}%"),
    ]
    print("🔄 Swap Details")
    for i, (label, val) in enumerate(details):
        end = "└─" if i == len(details) - 1 else "├─"
        print(f"{end} {label}: {val}")

    try:
        pair_token = web3_http.to_checksum_address(os.getenv("USDC_WETH_POOL"))
        reserve_usdc, reserve_weth, usdc_decimals, reserve_weth, price_weth_in_usdc, price_usdc_in_weth, market_price, mainnet_price_usdc = get_liquidity_and_price(web3_http, pair_token)
        amount_in_victim = transaction["value"]
        out_weth, price_before, price_after, impact = simulate_swap(
            reserve_usdc, reserve_weth, amount_in_victim
        )
        print(f"\n🔄  Simulating swap of {amount_in_victim / 10 ** usdc_decimals:.5f} USDC →")
        print(f"   • You get      ≃ {out_weth / 10 ** weth_decimals:.5f} WETH")
        print(f"   • New price    ≃ {price_after:.5f} WETH/USDC")
        print(f"   • Price impact ≃ {impact * 100:.5f}%")
        print(f"   • Equivalent Market   ≃ ${((1 / price_after) * mainnet_price_usdc):.5f} USD")
        slippage_tol: float = 0.015
        max_usdc_mev = max_input_for_slippage(
            reserve_weth, reserve_usdc, tol=slippage_tol
        )
        max_weth = simulate_swap(reserve_usdc, reserve_weth, max_usdc_mev)[0]
        print(f"\n🔒  To keep slippage ≤ {slippage_tol * 100:.5f}%:")
        print(f"   • Max input    ≃ {max_usdc_mev / 10 ** usdc_decimals:.5f} USDC")
        print(f"   • You’d get    ≃ {max_weth / 10 ** weth_decimals:.5f} WETH")
        print(f"   • Price moves  ≃ {price_before:.15f} → "
              f"{simulate_swap(reserve_usdc, reserve_weth, max_usdc_mev)[2]:.15f} WETH/USDC")
        profit = simulate_front_run_profit(
            reserve_usdc,
            reserve_weth,
            amount_in_victim,
            max_usdc_mev,
            fee_percentage=fee_pct_value
        )
        print(f"💰 Estimated MEV profit: {profit:.10f} USDC")
        #print("🚀 Front-run sent:", sent.hex())
    except Exception as e:
        print("❌ Error executing transaction:", str(e))
