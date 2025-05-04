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

    def send_add_liquidity(self):
        """User role: broadcast an AddLiquidityTx to introduce initial liquidity to the pool."""
        tx = AddLiquidityTx(provider="user", token_a="TokenA", amount_a=100, token_b="TokenB", amount_b=100)
        # Add to own mempool and send to peers
        self.mempool.append(tx)
        for peer in self.get_peers():
            self.ez_send(peer, tx)
        print("* User adding liquidity: 100 TokenA and 100 TokenB (broadcast AddLiquidityTx)")
    def send_whale_swap(self):
        """Whale role: broadcast a large SwapTx (TokenA -> TokenB) to simulate a big trade."""
        tx = SwapTx(trader="whale", from_token="TokenA", to_token="TokenB", amount_in=50)
        self.mempool.append(tx)
        for peer in self.get_peers():
            self.ez_send(peer, tx)
        print(f"* Whale swapping {tx.amount_in} {tx.from_token} for {tx.to_token} (broadcast SwapTx)")

        # --- Mining logic (for miner role) ---

    def mine_block(self):
        """Miner role: package pending transactions into a new block and broadcast it."""
        if not self.mempool:
            return  # nothing to include
        # Order transactions: ensure AddLiquidity comes before Swaps, and sniper's swaps get priority
        add_liqs = [tx for tx in self.mempool if isinstance(tx, AddLiquidityTx)]
        others = [tx for tx in self.mempool if not isinstance(tx, AddLiquidityTx)]
        # Sort others so that any SwapTx from sniper is placed before others (simulating front-run)
        others.sort(key=lambda tx: 0 if (hasattr(tx, "trader") and tx.trader == "sniper") else 1)
        ordered_txs = add_liqs + others
        # Create new Block
        prev_block = self.chain[-1]
        new_index = prev_block.index + 1
        new_block = Block(index=new_index, prev_hash=prev_block.hash, timestamp=time.time(),
                          transactions=ordered_txs)
        new_block.compute_hash()
        # Apply each transaction to update ledger and pool state
        for tx in ordered_txs:
            if isinstance(tx, TransferTx):
                # Simple token transfer
                if tx.amount <= self.ledger[tx.sender][tx.token]:
                    self.ledger[tx.sender][tx.token] -= tx.amount
                    self.ledger[tx.recipient][tx.token] += tx.amount
            elif isinstance(tx, AddLiquidityTx):
                # Liquidity added: deduct from provider and add to pool reserves
                if tx.amount_a <= self.ledger[tx.provider][tx.token_a] and tx.amount_b <= self.ledger[tx.provider][
                    tx.token_b]:
                    self.ledger[tx.provider][tx.token_a] -= tx.amount_a
                    self.ledger[tx.provider][tx.token_b] -= tx.amount_b
                    self.pool_reserves[tx.token_a] += tx.amount_a
                    self.pool_reserves[tx.token_b] += tx.amount_b
                    print(f"-> Pool created with reserves: {self.pool_reserves}")
            elif isinstance(tx, SwapTx):
                # Swap execution using constant product formula x*y=k
                token_in, token_out = tx.from_token, tx.to_token
                amount_in = tx.amount_in
                # Only execute if trader has enough balance
                if amount_in <= self.ledger[tx.trader][token_in] and self.pool_reserves[token_in] >= 0 and \
                        self.pool_reserves[token_out] > 0:
                    # Deduct input tokens from trader into pool
                    self.ledger[tx.trader][token_in] -= amount_in
                    X = self.pool_reserves[token_in] + amount_in  # new reserve of input token
                    Y = self.pool_reserves[token_out]
                    # Constant product invariant: X_new * Y_new = X_old * Y_old (k)
                    # Solve for Y_new = k / X_new, then output = Y_old - Y_new
                    if self.pool_reserves[token_in] == 0:
                        # Edge case: if pool had 0 of input token (shouldn't happen for normal use)
                        self.pool_reserves[token_in] = X
                        output_amount = 0
                    else:
                        k = self.pool_reserves[token_in] * self.pool_reserves[token_out]
                        Y_new = k / X
                        output_amount = Y - Y_new
                        # Update pool reserves
                        self.pool_reserves[token_in] = X
                        self.pool_reserves[token_out] = Y_new
                    # Credit output tokens to trader
                    output_amount_int = output_amount  # can cast to int if desired
                    self.ledger[tx.trader][token_out] += output_amount_int
                    print(
                        f"-> Swap executed for {tx.trader}: {amount_in} {token_in} -> {output_amount_int:.2f} {token_out}")
        # Append the new block to chain
        self.chain.append(new_block)
        # Clear mempool (all pending transactions are now in this block)
        self.mempool.clear()
        # Broadcast the BlockMessage to other peers
        block_data = [{"type": "transfer", **tx.__dict__} if isinstance(tx, TransferTx) else
                      {"type": "add_liquidity", **tx.__dict__} if isinstance(tx, AddLiquidityTx) else
                      {"type": "swap", **tx.__dict__}
                      for tx in ordered_txs]
        block_msg = BlockMessage(index=new_block.index, prev_hash=new_block.prev_hash,
                                 timestamp=new_block.timestamp, block_hash=new_block.hash,
                                 tx_data=json.dumps(block_data))
        for peer in self.get_peers():
            self.ez_send(peer, block_msg)
        print(
            f"*** Mined Block {new_block.index} with {len(ordered_txs)} transaction(s), broadcasting to network...")

        # --- Message Handlers for incoming messages ---

        @lazy_wrapper(TransferTx)
        def on_transfer_tx(self, peer, payload: TransferTx):
            """Handle incoming TransferTx: add to mempool."""
            self.mempool.append(payload)
            print(
                f"[Mempool] Received transfer of {payload.amount} {payload.token} from {payload.sender} to {payload.recipient}")


