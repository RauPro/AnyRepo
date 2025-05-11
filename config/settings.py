import os
import sys
from dotenv import load_dotenv

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
