import json
import os

import requests

from services import establish_quicknode_http_connection


def get_liquidity(web3, weth_address, usdc_address):
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
    usdc_decimals = 6
    weth_decimals = 6
    price_weth_in_usdc = (reserve_usdc / 10 ** usdc_decimals) / (reserve_weth / 10 ** weth_decimals)
    price_usdc_in_weth = (reserve_weth / 10 ** weth_decimals) / (reserve_usdc / 10 ** usdc_decimals)
    print("Total reserve WETH:",reserve_weth / 10**18)
    print("Total reserve USDC:", reserve_usdc / 10**18)
    print(f"1 WETH ≃ {price_weth_in_usdc:.2f} USDC")
    print(f"1 USDC ≃ {price_usdc_in_weth:.5f} USDC")
    mainnet_usdc = fetch_token_data(usdc_address)["data"]["attributes"]["price_usd"]
    print(f"1 WETH ≃ ${price_weth_in_usdc * float(mainnet_usdc)} US")


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