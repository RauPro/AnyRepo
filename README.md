# AnyRepo

- Raul Ernesto Guillen Hernandez
- Fernando Daniel González Batarsé
- Aleksandr Zvonarev


# 🦄 MEV Bot

## Overview
The **Uniswap MEV Bot** is a Python-based toolkit that 👀 **watches the Sepolia mempool** through a QuickNode WebSocket, decodes each pending Uniswap V2 swap, simulates its price impact with the constant-product invariant *x × y = k*, and projects potential sandwich-attack profit.  
When the projected gain beats a user-defined threshold, the bot (optionally) submits an on-chain test swap and writes all detected opportunities to `output/swaps.json` while printing a gas-sorted table in real time.

---

## 📂 Project Structure

### 📂 Project Structure
```text
CS411-Blockchain/
├── abi/            # JSON ABIs (UniswapV2Router02, ERC-20, …)
├── config/         # .env example + YAML/JSON settings templates
├── core/           # Orchestration: mempool listener, decoder, simulator
├── data/           # Reserve snapshots & token metadata for dry runs
├── lib/            # Thin wrappers around web3.py & eth-abi
├── services/       # QuickNode WSS/HTTP clients, GeckoTerminal feed
├── utils/          # Logging, PrettyTable, math utils, gas estimator
├── output/         # Auto-generated logs & swaps.json
├── main.py         # CLI entry-point – `python main.py`
└── requirements.txt
```
---

## ⚙️ Tech Stack
| Layer | Frameworks / Packages |
|-------|-----------------------|
| Blockchain  | **Ethereum Sepolia** testnet |
| Node Access | **QuickNode** HTTP + WebSocket |
| Python IO   | `asyncio`, `aiohttp`, `web3.py 6.x`, `eth-abi`, `eth-utils` |
| Config      | `python-dotenv`, `PyYAML` |
| Math / Tables | `decimal`, `prettytable`, `numpy` |
| Dev Tools   | `pytest`, `ruff`, `black` |

---

## 🧠 Strategy

1. **Mempool Surveillance**  
    • Open a persistent QuickNode WSS subscription to `newPendingTransactions`  
    • Discard hashes that don’t target **UniswapV2Router02** or have unknown 4-byte selectors :contentReference[oaicite:2]{index=2}  

2. **Slippage & Profit Simulation**  
    • Fetch pair reserves (`getReserves`) and apply  
    &nbsp;&nbsp;&nbsp;&nbsp;**Price before** = *reserve<sub>out</sub> / reserve<sub>in</sub>*  
    &nbsp;&nbsp;&nbsp;&nbsp;**Amount out** =   
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;`(amount_in·γ · reserve_out) / (reserve_in + amount_in·γ)` where γ = 0.997  
    • Repeat for a hypothetical **front-run + victim + back-run** sequence to get ΔUSDC profit :contentReference[oaicite:3]{index=3}  

3. **(Optional) Test Execution**  
    • If `profit_usd > PROFIT_THRESHOLD`, build & sign `swapExactETHForTokens` with a bump-gas price and push over HTTP  
    • Convert returns to USD via **GeckoTerminal** spot quotes :contentReference[oaicite:4]{index=4}  

4. **Result Aggregation**  
    • Rank opportunities by `effective_gas_price`  
    • Pretty-print to console and append to `output/swaps.json` (one JSON object per line)

---

### 🔐 Configuration

| Variable | Description |
|----------|-------------|
| `QUICKNODE_WSS` | Your **WebSocket** endpoint (Sepolia) |
| `QUICKNODE_HTTP` | Same node, **HTTP RPC** URL |
| `ACCOUNT_PK` | *Test-only* private key used for signing |
| `PROFIT_THRESHOLD` | Minimum USD profit to trigger a test swap |
| `TARGET_TOKENS` | Comma-separated list of ERC-20 addresses to track |

> All sensitive values stay in `.env`; everything else lives in `config/settings.yaml`.

---

## 🚀 Quick Start

```bash
# 1 Clone
git clone https://github.com/RauPro/CS411-Blockchain.git
cd CS411-Blockchain

# 2 Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3 Configure
cp config/.env.example .env          # fill in QUICKNODE_HTTP / QUICKNODE_WSS
nano config/settings.yaml            # tweak PROFIT_THRESHOLD, TOKENS, etc.

# 4 Run
python main.py                       # 🚴‍♂️ watch the mempool roll by
```

