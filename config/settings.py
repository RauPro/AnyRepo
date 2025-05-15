import os
import sys
from dotenv import load_dotenv
from eth_account import Account
from prettytable import PrettyTable
from web3 import Web3

load_dotenv()

def require_env(var_name, message=None):
    value = os.getenv(var_name)
    if not value:
        sys.exit(message or f"🔑 Please add your {var_name.lower()} to the .env file to continue!")
    return value

ACCOUNT_PRIVATE_KEY = require_env("ACCOUNT_PRIVATE_KEY")
QUICK_NODE_HTTP_URL = require_env("QUICK_NODE_HTTP_URL")
QUICK_NODE_WSS_URL = require_env("QUICK_NODE_WSS_URL")
CHAIN_ID_NUMBER = require_env("CHAIN_ID_NUMBER")
ROUTER_ADDRESS = require_env("ROUTER_ADDRESS")
USDC_TOKEN = require_env("USDC_TOKEN")
WETH_TOKEN = require_env("WETH_TOKEN")
GECKOTERMINAL_API = require_env("GECKOTERMINAL_API")
NETWORK = require_env("NETWORK")
FACTORYV2 = require_env("FACTORYV2")
USDC_WETH_POOL = require_env("USDC_WETH_POOL")

CHAIN_ID = int(CHAIN_ID_NUMBER)
ROUTER_CHECKSUM_ADDRESS = Web3.to_checksum_address(ROUTER_ADDRESS)
ACCOUNT = Account.from_key(ACCOUNT_PRIVATE_KEY)

t = PrettyTable(["Name", "Value"])
t._max_width = {"Name": 50, "Value": 75}
t.hrules = True
t.add_row(["Account address", ACCOUNT.address])
t.add_row(["Account private key", ACCOUNT_PRIVATE_KEY])
t.add_row(["Quick Node HTTP URL", QUICK_NODE_HTTP_URL])
t.add_row(["Quick Node WSS URL", QUICK_NODE_WSS_URL])
t.add_row(["Chain ID", CHAIN_ID_NUMBER])
t.add_row(["Router address", ROUTER_ADDRESS])
t.add_row(["USDC Token", USDC_TOKEN])
t.add_row(["WETH Token", WETH_TOKEN])
t.add_row(["GeckoTerminal API", GECKOTERMINAL_API])
t.add_row(["Network", NETWORK])
t.add_row(["FactoryV2", FACTORYV2])
t.add_row(["USDC/WETH Pool", USDC_WETH_POOL])

print(t)