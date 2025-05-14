import json
import os

import requests

from services import establish_quicknode_http_connection



def simulate_swap(reserve_in: float,
                  reserve_out: float,
                  amount_in: float,
                  fee: float = 0.003):
    """
    UniswapV2 constant-product swap:
      input:  amount_in  (WETH)
      reserves: reserve_in (WETH), reserve_out (USDC)
      fee: 0.003 (0.3%)

    returns: (amount_out, price_before, price_after, price_impact)
    """
    amount_in_with_fee = amount_in * (1 - fee)
    amount_out = (amount_in_with_fee * reserve_out) / (reserve_in + amount_in_with_fee)
    price_before = reserve_out / reserve_in
    price_after  = (reserve_out - amount_out) / (reserve_in + amount_in_with_fee)
    price_impact = (price_before - price_after) / price_before
    return amount_out, price_before, price_after, price_impact

def max_input_for_slippage(reserve_in: float,
                           reserve_out: float,
                           tol: float = 0.0005,
                           fee: float = 0.003,
                           max_fraction: float = 0.5,
                           iters: int = 15):
    """
    Binary-search the largest amount_in (≤ max_fraction * reserve_in)
    whose price_impact ≤ tol.
    """
    lo, hi = 0.0, reserve_in * max_fraction
    for _ in range(iters):
        mid = (lo + hi) / 2
        _, _, _, impact = simulate_swap(reserve_in, reserve_out, mid, fee)
        print(impact)
        if impact <= tol:
            lo = mid
        else:
            hi = mid
    return lo

def simulate_front_run_profit(reserve_usdc: float,
                              reserve_weth: float,
                              victim_amount_usdc: float,
                              mev_amount_usdc: float,
                              fee: float = 0.003):
    mev_weth, _, _, _ = simulate_swap(reserve_usdc,
                                      reserve_weth,
                                      mev_amount_usdc,
                                      fee)
    amount_in_with_fee = mev_amount_usdc * (1 - fee)
    reserve_usdc_1 = reserve_usdc + amount_in_with_fee
    reserve_weth_1 = reserve_weth - mev_weth
    victim_weth, _, _, _ = simulate_swap(reserve_usdc_1,
                                         reserve_weth_1,
                                         victim_amount_usdc,
                                         fee)
    victim_in_with_fee = victim_amount_usdc * (1 - fee)
    reserve_usdc_2 = reserve_usdc_1 + victim_in_with_fee
    reserve_weth_2 = reserve_weth_1 - victim_weth
    usdc_back, _, _, _ = simulate_swap(reserve_weth_2,
                                       reserve_usdc_2,
                                       mev_weth,
                                       fee)
    profit_usdc = usdc_back - mev_amount_usdc
    return profit_usdc

def get_liquidity_and_slippage(web3,
                               weth_address,
                               usdc_address,
                               weth_amount: float,
                               slippage_tol: float = 0.005):
    FACTORY = os.getenv("FACTORY_V2")
    factory = web3.eth.contract(FACTORY,
                                abi=json.load(open("abi/UniswapV2Factory.json", "r"))["abi"])
    #PAIR_POOL = factory.functions.getPair(weth_address, usdc_address).call() this should be used in real env
    PAIR_POOL = os.getenv("USDC_WETH_POOL")
    pair = web3.to_checksum_address(PAIR_POOL)
    contract = web3.eth.contract(address=pair, abi=json.load(open("abi/UniswapV2Pair.json", "r"))["abi"])
    reserves = contract.functions.getReserves().call()
    reserve_usdc = reserves[0]
    reserve_weth = reserves[1]
    out_usdc, price_before, price_after, impact = simulate_swap(
        reserve_usdc, reserve_weth, weth_amount
    )
    max_weth = max_input_for_slippage(
        reserve_weth, reserve_usdc, tol=slippage_tol
    )
    max_usdc = simulate_swap(reserve_weth, reserve_usdc, max_weth)[0]
    usdc_decimals = 6
    weth_decimals = 6
    price_weth_in_usdc = (reserve_usdc / 10 ** usdc_decimals) / (reserve_weth / 10 ** weth_decimals)
    price_usdc_in_weth = (reserve_weth / 10 ** weth_decimals) / (reserve_usdc / 10 ** usdc_decimals)
    mainnet_price_usdc = float(fetch_token_data(usdc_address)["data"]["attributes"]["price_usd"])
    print(f"🦄  Total reserve WETH:   {reserve_weth / 10 ** 18:.5f} ")
    print(f"💵  Total reserve USDC:   {reserve_usdc / 10 ** 18:.5f} ")
    print("\n📈  Price Before Swap")
    print(f"   • 1 WETH  ≃ {price_weth_in_usdc:.5f} USDC")
    print(f"   • 1 USDC  ≃ {price_usdc_in_weth:.5f} WETH")
    print(f"   • Market  ≃ {price_weth_in_usdc * mainnet_price_usdc:.5f} US")
    print(f"\n🔄  Simulating swap of {weth_amount / 10 ** 6:.5f} USDC →")
    print(f"   • You get      ≃ {out_usdc / 10 ** 6:.5f} WETH")
    print(f"   • New price    ≃ {price_after:.5f} WETH/USDC")
    print(f"   • Price impact ≃ {impact * 100:.5f}%")

    print(f"   • Equivalent   ≃ ${((1  / price_after)  * mainnet_price_usdc):.5f} USD")

    print(f"\n🔒  To keep slippage ≤ {slippage_tol * 100:.5f}%:")
    print(f"   • Max input    ≃ {max_weth:.5f} USDC")
    print(f"   • You’d get    ≃ {max_usdc:.5f} WETH")
    print(f"   • Price moves  ≃ {price_before:.15f} → "
          f"{simulate_swap(reserve_usdc, reserve_weth, max_weth)[2]:.15f} WETH/USDC")


def fetch_token_data(usdc_address):
    GECKOTERMINAL_API = os.getenv("GECKOTERMINAL_API")
    NETWORK  = os.getenv("NETWORK")
    url = f'{GECKOTERMINAL_API}/{NETWORK}/tokens/{usdc_address}'
    headers = {
        'accept': 'application/json'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()