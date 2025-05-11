import os
import sys
from dotenv import load_dotenv
from eth_account import Account
from prettytable import PrettyTable
from web3 import Web3

load_dotenv()

ACCOUNT_PRIVATE_KEY = os.getenv("ACCOUNT_PRIVATE_KEY")

if not (ACCOUNT_PRIVATE_KEY):
    sys.exit("🔑 Please add your private key to the .env file to continue!")

QUICK_NODE_HTTP_URL = os.getenv("QUICK_NODE_HTTP_URL")

if not (QUICK_NODE_HTTP_URL):
    sys.exit("🔑 Please add your quick node http url to the .env file to continue!")

QUICK_NODE_WSS_URL = os.getenv("QUICK_NODE_WSS_URL")

if not (QUICK_NODE_WSS_URL):
    sys.exit("🔑 Please add your quick node wss url to the .env file to continue!")

CHAIN_ID_NUMBER = os.getenv("CHAIN_ID_NUMBER")

if not (CHAIN_ID_NUMBER):
    sys.exit("🔑 Please add your chain id to the .env file to continue!")

ROUTER_ADDRESS = os.getenv("ROUTER_ADDRESS")

if not (ROUTER_ADDRESS):
    sys.exit("🔑 Please add your router address to the .env file to continue!")

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

print(t)
