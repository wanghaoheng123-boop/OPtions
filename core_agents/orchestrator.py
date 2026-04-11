import os
import json
from skills.backtester import StrategyBacktester
from skills.researcher_skill import GitHubResearcher
from skills.meta_model import MetaLabeler
from memory.db_setup import LocalMemoryStore

class MarketExpertTeam:
    """
    Agent Orchestration Layer integrating Researcher, Trader, Developer, and Critic loops.
    Designed to accept standard OpenAI/OpenSource LLM clients. Defaults to algorithmic proxies here 
    if strictly deterministic generation is preferred without an API key.
    """
    
    SYSTEM_PROMPTS = {
        "Trader": "You are an Institutional Options Trader. Use the provided Call Wall and Gamma Exposure to pick one strategy: 'short_put', 'covered_call', or 'long_gamma'.",
        "Critic": "You are a quantitative Risk Manager. You review the Trader's logic and the AP Backtester's historic results. Reject ANY strategy with a drawdown > 20%. No hallucinations.",
    }

    @staticmethod
    def get_trader_analysis(market_structure: dict, research_context: dict) -> dict:
        """
        The Options Trader Persona. Evaluates strategy based on GEX and Call/Put walls
        and applies Researcher's GitHub algorithms.
        """
        net_gex = market_structure.get("total_net_gex", 0)
        call_wall = market_structure.get("call_wall_strike", 0)
        
        # Simulated LLM generation based on system prompt and data
        if net_gex > 0:
            strategy = "covered_call"
            insight = (
                f"Dealer Gamma is positive. Incorporating {research_context['name']}: market makers will buy dips "
                f"suppressing volatility. A range-bound strategy like 'covered_call' near '{call_wall}' is preferred."
            )
        else:
            strategy = "long_gamma"
            insight = (
                f"Dealer Gamma is negative. Incorporating {research_context['name']}: makers sell weakness. "
                "Volatility is expanding. Initiate long variance 'long_gamma'."
            )
            
        return {"strategy_selected": strategy, "insight": insight}

    @staticmethod
    def get_critic_review(trader_insight: str, backtest_result: dict) -> str:
        """
        The Independent Review (Critic/Risk) loop. Blocks hallucinated success.
        """
        if "error" in backtest_result:
            return f"CRITIC REJECTED: Backtest execution failed. {backtest_result['error']}"
            
        verdict = backtest_result.get("verdict", "FAIL")
        drawdown = backtest_result.get("max_drawdown", 100)
        
        if verdict == "PASS" and drawdown < 20.0:
            return f"CRITIC APPROVED: The {backtest_result['strategy_tested']} strategy historically returned a profit without breaching risk limits (Drawdown: {drawdown}%)."
        else:
            return f"CRITIC REJECTED: The strategy exhibited excessive risk or negative expectancy (Drawdown: {drawdown}%, Verdict: {verdict}). Do not execute."

    @classmethod
    def run_agentic_loop(cls, ticker: str, market_data: dict) -> dict:
        memory_store = LocalMemoryStore()
        
        def mock_llm_query(prompt: str, role: str, market_structure_data: dict, bkt_verdict: str = "") -> str:
            # In production, replace with `google.generativeai.generate_content`
            
            # Check for RAG document
            rag_context = ""
            kb_path = os.path.join(os.path.dirname(__file__), "knowledge", "QUANT_KNOWLEDGE_BASE.md")
            if os.path.exists(kb_path):
                with open(kb_path, "r", encoding="utf-8") as f:
                    rag_context = f.read()

            # Mock LLM Responses strictly aligning to RAG instructions
            if role == "trader":
                if "extreme fear" in market_structure_data.get('volatility_skew', {}).get('sentiment', '').lower():
                    return "Market exhibits Extreme Fear. Executing Cash-Secured Puts (Wheel) deep OTM as dictated by QUANT_KNOWLEDGE_BASE."
                else:
                    return "Deploying Iron Condor (Net Volatility Seller) framework due to systemic IV overstatement verified by QUANT_KNOWLEDGE_BASE."
            elif role == "critic":
                if bkt_verdict == "FAIL":
                    return "DISAPPROVED: Strategy failed strict 80% Win Rate and >1.2 Profit Factor metrics out-of-sample constraint."
                return "APPROVED: Asymmetric risk contained. Expectancy structural edge intact. Execution authorized."
            else:
                return f"{role.capitalize()} Agent computed data structure."

        # 1. Researcher Output
        research_context = GitHubResearcher.fetch_relevant_algorithm("GEX")
        
        # 2. Trader Proposes Strategy
        trader_insight = mock_llm_query(f"Ticker: {ticker}. Mkt Structure: {json.dumps(market_data)}. Devise structural premium strategy.", "trader", market_data)
        
        # Phase 6: Core Engine mapping to knowledge-base strategies
        strat_map = "iron_condor"
        if "wheel" in trader_insight.lower() or "puts" in trader_insight.lower():
            strat_map = "wheel"
            
        backtest = StrategyBacktester.run_historical_backtest(ticker, strat_map, days=180)
        bkt_verdict = backtest.get("verdict", "FAIL")
        
        # Phase 7: Meta Labeling (Secondary ML Override)
        # We proxy a meta-label prediction. If market sentiment is highly adverse to the spread, 
        # the meta-model zeroes the bet.
        meta_label_score = 1.0
        sentiment = market_data.get('volatility_skew', {}).get('sentiment', '').lower()
        if strat_map == 'iron_condor' and 'extreme' in sentiment:
            meta_label_score = 0.0 # Meta model overrides the Iron Condor during extreme spikes
        elif strat_map == 'wheel' and 'greed' in sentiment:
            meta_label_score = 0.0 # Don't sell puts when market is euphoric (reversal risk)
            
        if meta_label_score < 0.5:
            bkt_verdict = "FAIL"
            critic_override = "CRITIC REJECTED: Meta-Labeling ML Model detects regime shift. Bet size reduced to 0."
        else:
            critic_override = mock_llm_query("Review backtest.", "critic", market_data, bkt_verdict)
        
        # 4. Critic Reviews
        critic_insight = critic_override
        
        # 5. Save to local Memory DB to learn
        memory_store.log_session(
            ticker=ticker,
            market_data=market_data,
            trader_insight=trader_insight,
            backtest_result=backtest,
            critic_review=critic_insight
        )
        
        return {
            "trader_insight": trader_insight,
            "researcher_context": research_context["logic_description"],
            "backtest": backtest,
            "critic_review": critic_insight
        }
