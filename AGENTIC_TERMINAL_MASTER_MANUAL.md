# Agentic Quant Terminal: Master Manual & Architecture Document

Welcome to the **Agentic Quant Terminal V2**, a fully autonomous, institutional-grade options analysis and trading suite powered by the principles of **Advances in Financial Machine Learning (AFML)** and deterministic Hedge Fund algorithms.

This system has evolved far beyond simple directional guessing or basic API fetches. It is a comprehensive mathematical engine designed to enforce an **80% win-rate edge** by strictly analyzing variance, market sentiment, and structural divergences.

---

## I. Architectural Components

### 1. Multi-Agent Artificial Intelligence (`core_agents/orchestrator.py`)
The system isolates quantitative tasks into specific autonomous agents:
*   **The Option Trader:** Proposes mathematical strategies based on Gamma Exposure (Dealer Positioning).
*   **The Researcher:** Searches GitHub schemas and macro structures for optimal execution logic.
*   **The Critic:** Acts as the institutional Risk Manager. It natively intercepts the logic from the trader, forces it through the Backtester, and **hard-rejects** any strategy generating a Profit Factor below 1.2 or a Max Drawdown over 20%.

### 2. The AFML Backtesting Core (`skills/backtester.py`)
Traditional retail algorithms use arbitrary stop losses. The Terminal utilizes Marcos Lopez de Prado's **Triple Barrier Labeling Method**.
*   It dynamically measures the current Exponentially Weighted Moving Volatility (EWMA).
*   It walks forward testing historical prices against an Upper (Profit) and Lower (Loss) barrier that expands or contracts mathematically based on market noise, preventing "false stops" while evaluating edge.

### 3. The Meta-Labeling Model (`skills/meta_model.py`)
The system incorporates **Scikit-Learn Random Forests** to act as a secondary sizing engine. 
*   Even if the mathematical backtester approves a trade, the machine learning classifier evaluates secondary anomalies (VIX Skew, Macro Events). If it identifies a shifting regime, the Meta-Model actively overrides the system and zeroes out the position size.

### 4. Institutional Statistical Arbitrage (`skills/statarb_scanner.py`)
Rather than solely relying on directional trades, the system constantly tracks massive, multi-billion-dollar cointegrated pairs (e.g., `SPY vs QQQ`, `Gold vs Silver`). 
*   It actively crunches their 90-Day rolling mean correlation and spits out the precise **Z-Score Spread**. 
*   If that Standard Deviation breaches `+/- 2.0`, the UI matrix flashes Red or Green, pinpointing algorithmic, market-neutral alpha.

### 5. Kelly Criterion AI Execution (`skills/paper_trader.py`)
When the Critic Agent approves a trade, it does not allocate a flat 10%. It takes the historically verified Win Rate from the backtest and parses it through the strict **Half-Kelly Formula**. The Terminal will mathematically allocate exact fractional weights scaled purely to the historical edge probability protecting you from ruin.

---

## II. The Quant Knowledge Base (RAG)
Located in `core_agents/knowledge/QUANT_KNOWLEDGE_BASE.md`.

This terminal is permanently bound to this physical markdown file. It contains the absolute grounding rules for all multi-agent computations. 
*   **Rule 1:** Net Volatility Selling (Iron Condors, Short Puts) is the only approved structure to hit 80% Expectancy.
*   **Rule 2:** IV Rank drives sizing. The AI is forbidden from buying premium when Implied Volatility is inflated.

*Any future models, algorithms, or scripts you wish the AI to adopt must be physically appended to this document.*

---

## III. Terminal Interface 

The frontend environment handles the intense mathematical output via a dense Bloomberg `CSS Grid` Layout.
1.  **Run Backend:** `.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`
2.  **Run Frontend:** `npm run dev`
3.  **UI Data Nodes:**
    *   **Top:** Global Ticker Search (Navigates Options Chains instantly).
    *   **Left Column:** Federal Reserve API Terminal & AI Portfolio Ledger.
    *   **Center:** Interactive TradingView charting overlaid with Gamma Wall Resistance/Support lines, flanked below by the independent AI consensus loops.
    *   **Right Column:** Global Sector Heatmap & Deep Implied Volatility (IV Skew) Fear/Greed Matrix.
    *   **Bottom Stack:** Fast-executing Statistical Arbitrage Pair Grid.

*Terminal Developed via Antigravity Automated Intelligence V3.*
