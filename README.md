# AnyRepo

- Raul Ernesto Guillen Hernandez
- Fernando Daniel González Batarsé
- Aleksandr Zvonarev


# MEV Bot

## Project Overview
This project aims to build a **Maximal Extractable Value (MEV) Bot** that leverages on‐chain opportunities to generate profit. By monitoring pending transactions in the mempool, the bot can execute sophisticated trading strategies—namely **Sandwich** and **Arbitrage**—across decentralized exchanges (DEXs).

## Key Strategies
1. **Sandwich Strategy**  
   - Detects large pending trades from other users.  
   - Places a “front-run” buy order just before the target trade, and a “back-run” sell order immediately after.  
   - Captures the price movement caused by the victim’s transaction.

2. **Arbitrage Strategy**  
   - Spots price discrepancies for the same asset between two different DEXs.  
   - Buys on the DEX where the asset is cheaper, then sells on the DEX where it’s more expensive.  
   - Locks in the spread as profit, accounting for fees.

## How It Works
1. **Sniper Over Mempool**  
   Continuously scan the pending transaction pool for high-impact trades.

2. **Identify Potential Targets**  
   Filter for large swaps or transactions likely to move market prices significantly.

3. **Buy at the Lower Price**  
   Execute a buy order on the DEX offering the best (lowest) price for the asset.

4. **Execute Against the Victim Trade**  
   - TBD

5. **Take Profit**  
   Collect the net gain from the price difference, minus any transaction or swap fees.

## Current Task Board
1. Sniper Over Mempool
- Fetch ETH mempool by using QuickNode and Web3
