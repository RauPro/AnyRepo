import json
import time
from ipv8.community import CommunitySettings, Community
from ipv8.lazy_community import lazy_wrapper
from merkle_tree import Block
from models import TransferTx, AddLiquidityTx, SwapTx, BlockMessage

class TokenCommunitySettings(CommunitySettings):
    role: str = "user"

class TokenCommunity(Community):
    community_id = b"randomteamwithrusian"
    settings_class = TokenCommunitySettings

    def __init__(self, settings: TokenCommunitySettings):
        super().__init__(settings)
        self.role = settings.role
        # Initialize chain, mempool, ledger, and pool reserves
        self.mempool = []                   # list of pending transactions (dataclass instances)
        self.seed_genesis_block()           # start with the predefined genesis block
        self.pool_reserves = {"TokenA": 0, "TokenB": 0}  # will populate when liquidity is added


        # Register message handlers for incoming payloads
        self.add_message_handler(TransferTx, self.on_transfer_tx)
        self.add_message_handler(AddLiquidityTx, self.on_add_liquidity_tx)
        self.add_message_handler(SwapTx, self.on_swap_tx)
        self.add_message_handler(BlockMessage, self.on_block_message)

    def seed_genesis_block(self):
        # Initialize a ledger for token balances and the blockchain (genesis block)
        initial_balances = {
            "miner": {"TokenA": 1000, "TokenB": 1000},
            "sniper": {"TokenA": 1000, "TokenB": 0},  # Sniper bot starts with TokenA only
            "user": {"TokenA": 1000, "TokenB": 500},  # Liquidity provider has some of both tokens
            "whale": {"TokenA": 1000, "TokenB": 0}  # "Whale" trader has TokenA to swap for TokenB
        }


        # Create genesis block with no transactions, fixed timestamp=0 for consistency across nodes
        genesis = Block(index=0, prev_hash="0", timestamp=0.0, transactions=[])
        genesis.compute_hash()
        blockchain = [genesis]  # list representing the chain
        self.chain = [genesis]
        ledger = initial_balances.copy()
        self.ledger = ledger.copy()  # copy initial balances

    def started(self) -> None:
        """Called when the community is fully initialized. Schedule any role-specific tasks."""
        for p in self.get_peers():
            print(p)
        # Only the miner will produce blocks
        if self.role == "miner":
            # Schedule mining two blocks at specific times (3s and 7s) for demonstration
            self.register_task("mine_block1", self.mine_block, delay=3.0, interval=0)
            self.register_task("mine_block2", self.mine_block, delay=7.0, interval=0)
        # The user (liquidity provider) will add liquidity after 2 seconds
        if self.role == "user":
            self.register_task("add_liquidity", self.send_add_liquidity, delay=2.0, interval=0)
        # The whale will perform a large swap after 5 seconds
        if self.role == "whale":
            self.register_task("whale_swap", self.send_whale_swap, delay=5.0, interval=0)

    # --- Message sending helper methods (for user/whale actions) ---

