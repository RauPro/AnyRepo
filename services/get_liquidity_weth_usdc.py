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
    mev_weth, price_before, _, _ = simulate_swap(
        reserve_usdc, reserve_weth, mev_amount_usdc, fee
    )
    usdc_per_weth_before = 1.0 / price_before
    in_with_fee = mev_amount_usdc * (1 - fee)
    r0 = reserve_usdc + in_with_fee
    r1 = reserve_weth - mev_weth
    _, _, price_after1, _ = simulate_swap(
        r0, r1, victim_amount_usdc, fee
    )
    usdc_per_weth_after1 = 1.0 / price_after1
    profit_usdc = mev_weth * (usdc_per_weth_after1 - usdc_per_weth_before)
    return profit_usdc / 10**18

def get_pool_reserves(web3, pair_address: str):
    """
    Fetch raw reserves (USDC, WETH) from on-chain UniswapV2Pair.
    Returns ints (reserve_usdc, reserve_weth).
    """
    abi = json.load(open("abi/UniswapV2Pair.json"))["abi"]
    contract = web3.eth.contract(address=web3.to_checksum_address(pair_address), abi=abi)
    reserve_usdc, reserve_weth, _ = contract.functions.getReserves().call()
    return reserve_usdc, reserve_weth


def get_liquidity_and_price(web3,
                            pair_token):
    #FACTORY = os.getenv("FACTORY_V2")
    #factory = web3.eth.contract(FACTORY, abi=json.load(open("abi/UniswapV2Factory.json", "r"))["abi"])
    #PAIR_POOL = factory.functions.getPair(weth_address, usdc_address).call() this should be used in real env
    reserve_usdc, reserve_weth = get_pool_reserves(web3, pair_token)
    usdc_address = web3.to_checksum_address(os.getenv("USDC_TOKEN"))
    usdc_decimals = 18
    weth_decimals = 18
    price_weth_in_usdc = (reserve_usdc / 10 ** usdc_decimals) / (reserve_weth / 10 ** weth_decimals)
    price_usdc_in_weth = (reserve_weth / 10 ** weth_decimals) / (reserve_usdc / 10 ** usdc_decimals)
    mainnet_price_usdc = float(fetch_token_data(usdc_address)["data"]["attributes"]["price_usd"])
    print(f"🦄  Total reserve WETH:   {reserve_weth / 10 ** 18:.5f} ")
    print(f"💵  Total reserve USDC:   {reserve_usdc / 10 ** 18:.5f} ")
    print("\n📈  Price Before Swap")
    print(f"   • 1 WETH  ≃ {price_weth_in_usdc:.5f} USDC")
    print(f"   • 1 USDC  ≃ {price_usdc_in_weth:.5f} WETH")
    print(f"   • Market  ≃ ${price_weth_in_usdc * mainnet_price_usdc:.5f} US")
    return reserve_usdc, reserve_weth, usdc_decimals, reserve_weth, price_weth_in_usdc, price_usdc_in_weth, price_weth_in_usdc * mainnet_price_usdc, mainnet_price_usdc




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