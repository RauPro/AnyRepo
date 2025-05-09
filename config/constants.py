import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

QUICK_NODE_URL = os.getenv("QUICK_NODE_URL")

ETHEREUM_SEPOLIA_CHAIN_ID = os.getenv("ETHEREUM_SEPOLIA_CHAIN_ID")
ETHEREUM_SEPOLIA_UNISWAP_V3_FACTORY_ADDRESS = os.getenv(
    "ETHEREUM_SEPOLIA_UNISWAP_V3_FACTORY_ADDRESS"
)
ETHEREUM_SEPOLIA_WETH9_ADDRESS = os.getenv("ETHEREUM_SEPOLIA_WETH9_ADDRESS")
USDC_ADDRESS = os.getenv("USDC_ADDRESS")

_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ABI_PATH = _DIR / "abi"
