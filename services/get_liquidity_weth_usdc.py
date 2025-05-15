import json
import os

import requests


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