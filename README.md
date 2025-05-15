# AnyRepo

- Raul Ernesto Guillen Hernandez
- Fernando Daniel González Batarsé
- Aleksandr Zvonarev


# MEV Bot

## Overview

The Uniswap MEV Bot is a Python tool that continuously monitors the Ethereum Sepolia mempool for Uniswap V2 swap transactions via QuickNode WebSocket streams ([QuickNode][1]). It decodes each pending transaction’s parameters against the UniswapV2Router02 ABI, simulates its price impact using the constant-product formula $x \times y = k$, and estimates potential MEV profit ([Uniswap Docs][2]). When profitable opportunities above a configured threshold are detected, the bot can optionally execute test swaps through the router contract over HTTP, then ranks and logs the highest-gas-price transactions in a PrettyTable and saves them to `output/swaps.json`.

## Strategy

1. **Mempool Surveillance**

   * Establish a persistent WebSocket connection to QuickNode to stream `newPendingTransactions` in real time ([QuickNode][3]).
   * Filter for transactions targeting the UniswapV2Router02 address and matching known swap function selectors.

2. **Slippage & Profit Simulation**

   * Apply the Uniswap V2 invariant $x \times y = k$ to compute:

     * **Price Before:** $\frac{reserve_{out}}{reserve_{in}}$
     * **Amount Out:** $\frac{(amount_{in}\times(1 - fee))\times reserve_{out}}{reserve_{in} + (amount_{in}\times(1 - fee))}$
     * **Price After:** $\frac{reserve_{out} - amount_{out}}{reserve_{in} + (amount_{in}\times(1 - fee))}$
     * **Price Impact:** $\frac{price_{before} - price_{after}}{price_{before}}$ ([Uniswap Docs][2], [Uniswap Docs][4]).
   * Model a front-run scenario by simulating both a MEV trade and the victim’s trade in sequence, then calculating net USDC profit.

3. **Optional Test Execution**

   * If simulated profit exceeds a user-defined cutoff, build and sign a `swapExactETHForTokens` transaction via Web3.py over HTTP.
   * Use GeckoTerminal’s API to fetch live on-chain price data as needed for USD conversions ([GeckoTerminal][5]).

4. **Result Aggregation**

   * Collected opportunities are sorted by gas price, presented in a console table, and persisted to JSON for analysis.

By combining real-time mempool filtering, on-chain price simulations, and optional test swaps, this strategy aims to capture small but frequent MEV gains around Uniswap V2 swaps.

[1]: https://www.quicknode.com/guides/ethereum-development/transactions/how-to-access-ethereum-mempool?utm_source=chatgpt.com "How to Access Ethereum Mempool | QuickNode Guides"
[2]: https://docs.uniswap.org/contracts/v2/concepts/protocol-overview/how-uniswap-works?utm_source=chatgpt.com "How Uniswap works"
[3]: https://www.quicknode.com/guides/infrastructure/how-to-manage-websocket-connections-on-ethereum-node-endpoint?utm_source=chatgpt.com "How to Manage WebSocket Connections With Your Ethereum Node ..."
[4]: https://docs.uniswap.org/contracts/v2/concepts/core-concepts/swaps?utm_source=chatgpt.com "Swaps - Uniswap Docs"
[5]: https://api.geckoterminal.com/docs/index.html?utm_source=chatgpt.com "GeckoTerminal API Docs"

