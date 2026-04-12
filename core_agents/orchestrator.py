import os
import json
import numpy as np
import pandas as pd
from skills.backtester import run_backtest as run_historical_backtest
from skills.researcher_skill import GitHubResearcher
from skills.meta_model import MetaLabeler
from skills.parameter_optimizer import ParameterOptimizer
from memory.db_setup import LocalMemoryStore


class MarketExpertTeam:
    """
    Agent Orchestration Layer integrating Researcher, Trader, Researcher, and Critic loops.
    Production version with real MetaLabeler integration and AFML-compliant pipeline.

    Flow:
    1. Researcher Agent → Fetch verified algorithm context
    2. Trader Agent → Propose strategy from GEX/skew analysis
    3. ParameterOptimizer → QuickScan for optimal barrier params
    4. StrategyBacktester → Triple Barrier historical backtest (OOS verified)
    5. MetaLabeler → ML override for regime shift detection
    6. Critic Agent → Final risk verdict (hard constraints: WR>=75%, PF>=1.2, DD<20%)
    7. Memory → Log session for future few-shot learning
    """

    SYSTEM_PROMPTS = {
        "Trader": (
            "You are an Institutional Options Trader. Use GEX, Call Wall, Put Wall, "
            "and Volatility Skew sentiment to propose one strategy: "
            "'short_put', 'wheel', 'covered_call', 'iron_condor', or 'long_gamma'. "
            "Follow QUANT_KNOWLEDGE_BASE Rule 1: only sell premium when IV Rank > 50."
        ),
        "Critic": (
            "You are a quantitative Risk Manager. Hard constraints: "
            "Win Rate >= 75%, Profit Factor >= 1.2, Max Drawdown < 20%, Sharpe >= 1.5. "
            "Reject any strategy violating these — no exceptions."
        ),
        "Researcher": (
            "You are a quant researcher. Fetch relevant algorithm context from the "
            "verified knowledge base and explain how it applies to current market conditions."
        )
    }

    # Strategy selection rules based on market conditions
    STRATEGY_RULES = {
        ("Bearish Protection", "Extreme Fear"): "wheel",
        ("Bearish Protection", "Moderate Skew"): "wheel",
        ("Bullish Greed", "Call Skew"): "iron_condor",
        ("Neutral Skew", "Neutral"): "iron_condor",
        ("Extreme Fear", "High Skew"): "covered_call",  # Sell call protection
        ("Extreme Fear", "Moderate Skew"): "covered_call",
    }

    @classmethod
    def select_strategy(cls, market_data: dict) -> str:
        """
        Rule-based strategy selection from market structure data.
        In production, this would be replaced by an LLM analyzing the same inputs.
        """
        skew_sentiment = market_data.get("volatility_skew", {}).get("sentiment", "Neutral")
        iv_rank_data = market_data.get("iv_rank") or {}
        iv_verdict = iv_rank_data.get("verdict", "NEUTRAL")

        # Check for extreme fear / high skew → wheel
        if "Fear" in skew_sentiment or iv_verdict == "SELL_PREMIUM":
            net_gex = market_data.get("total_net_gex", 0)
            if net_gex < 0:
                return "wheel"  # Negative gamma (dealers short) → sell puts
            else:
                return "short_put"  # Positive gamma → sell OTM puts

        # Check for neutral / low skew → iron condor
        if "Neutral" in skew_sentiment or abs(iv_rank_data.get("iv_rank", 50)) < 20:
            return "iron_condor"

        # Check for greed / call skew → covered call
        if "Greed" in skew_sentiment:
            return "covered_call"

        # Default: iron condor (neutral net volatility seller)
        return "iron_condor"

    @classmethod
    def get_trader_insight(cls, ticker: str, market_data: dict, strategy: str,
                           research_context: dict) -> str:
        """
        Generate trader reasoning based on market structure.
        """
        net_gex = market_data.get("total_net_gex", 0)
        call_wall = market_data.get("call_wall_strike", 0)
        put_wall = market_data.get("put_wall_strike", 0)
        spot = market_data.get("spot_price", 0)
        sentiment = market_data.get("volatility_skew", {}).get("sentiment", "Neutral")

        algo_name = research_context.get("name", "Standard")

        if strategy == "wheel":
            return (
                f"SPY at {spot:.2f}. Negative GEX ({net_gex/1e6:.1f}M). "
                f"Extreme Fear skew detected. "
                f"Implementing Cash-Secured Puts near ${put_wall:.0f} strike. "
                f"Algo: {algo_name} — dealers sell into panic, collect premium."
            )
        elif strategy == "iron_condor":
            return (
                f"SPY at {spot:.2f}. Neutral skew ({sentiment}). "
                f"Call Wall ${call_wall:.0f}, Put Wall ${put_wall:.0f}. "
                f"Deploying Iron Condor — net volatility seller framework. "
                f"Algo: {algo_name} — IV overstatement creates premium edge."
            )
        elif strategy == "covered_call":
            return (
                f"SPY at {spot:.2f}. Bullish Greed sentiment. "
                f"Call Wall ${call_wall:.0f}. "
                f"Covered Call at Call Wall — collect premium above market. "
                f"Algo: {algo_name}."
            )
        elif strategy == "short_put":
            return (
                f"SPY at {spot:.2f}. Positive GEX ({net_gex/1e6:.1f}M). "
                f"Selling OTM puts below Put Wall ${put_wall:.0f}. "
                f"Algo: {algo_name}."
            )
        else:
            return f"Deploying {strategy} strategy per market analysis."

    @classmethod
    def get_critic_review(cls, backtest_result: dict, meta_result: dict = None) -> dict:
        """
        Independent risk review. Hard constraints must ALL be satisfied.
        """
        verdict_map = {
            True: "APPROVED",
            False: "REJECTED"
        }

        if "error" in backtest_result:
            return {
                "verdict": "REJECTED",
                "reason": f"Backtest failed: {backtest_result['error']}",
                "metric_breakdown": {}
            }

        # Extract metrics
        win_rate = backtest_result.get("win_rate_percent", 0)
        profit_factor = backtest_result.get("profit_factor", 0)
        max_drawdown = backtest_result.get("max_drawdown", 100)
        sharpe = backtest_result.get("sharpe_ratio", 0)
        sortino = backtest_result.get("sortino_ratio", 0)
        calmar = backtest_result.get("calmar_ratio", 0)

        # Hard constraints
        constraints = {
            "win_rate >= 75%": win_rate >= 75.0,
            "profit_factor >= 1.2": profit_factor >= 1.2,
            "max_drawdown < 20%": max_drawdown < 20.0,
        }

        # Soft constraints (warnings)
        soft_constraints = {
            "sharpe_ratio >= 1.5": sharpe >= 1.5,
            "sortino_ratio >= 1.0": sortino >= 1.0,
            "calmar_ratio >= 1.0": calmar >= 1.0,
        }

        all_hard_passed = all(constraints.values())

        # Meta-model override
        meta_passed = True
        if meta_result:
            meta_verdict = meta_result.get("verdict", "APPROVE")
            meta_passed = (meta_verdict == "APPROVE")
            if not meta_passed:
                all_hard_passed = False
                constraints["meta_model_regime"] = False

        final_verdict = all_hard_passed and meta_passed

        # Build detailed breakdown
        metric_breakdown = {
            "win_rate": f"{win_rate:.1f}%",
            "profit_factor": f"{profit_factor:.2f}",
            "max_drawdown": f"{max_drawdown:.1f}%",
            "sharpe_ratio": f"{sharpe:.2f}",
            "sortino_ratio": f"{sortino:.2f}",
            "calmar_ratio": f"{calmar:.2f}",
            "num_trades": backtest_result.get("num_trades", 0),
            "trained_volatility": f"{backtest_result.get('trained_volatility', 0):.6f}",
            "barrier_hits": backtest_result.get("barrier_hits", {})
        }

        if meta_result:
            metric_breakdown["meta_bet_size"] = f"{meta_result.get('bet_size', 1.0):.4f}"
            metric_breakdown["meta_confidence"] = meta_result.get("confidence", "unknown")

        # Reason string
        if final_verdict:
            reason = (
                f"APPROVED: All risk constraints satisfied. "
                f"WR={win_rate:.1f}% (>=75%), PF={profit_factor:.2f} (>=1.2), "
                f"DD={max_drawdown:.1f}% (<20%)"
            )
        else:
            failed = [k for k, v in constraints.items() if not v]
            reason = f"REJECTED: Failed constraints: {', '.join(failed)}"

        return {
            "verdict": verdict_map[final_verdict],
            "reason": reason,
            "metric_breakdown": metric_breakdown,
            "hard_constraints_passed": all_hard_passed,
            "meta_model_passed": meta_passed,
            "constraint_detail": constraints,
            "soft_constraint_warnings": {k: v for k, v in soft_constraints.items() if not v}
        }

    @classmethod
    def run_agentic_loop(cls, ticker: str, market_data: dict,
                         days: int = 180,
                         use_meta_model: bool = True,
                         use_optimization: bool = True) -> dict:
        """
        Main agentic loop. Coordinates all agents and returns comprehensive analysis.

        Args:
            ticker: Instrument to analyze (e.g., 'SPY')
            market_data: Dict from MarketStructureAnalyzer + VolatilitySkewAnalyzer
            days: Historical backtest lookback period
            use_meta_model: Whether to apply ML regime override
            use_optimization: Whether to run ParameterOptimizer QuickScan first

        Returns:
            Full analysis including trader insight, researcher context,
            backtest results, meta-model verdict, and critic review.
        """
        # Step 1: Researcher Agent - Fetch algorithm context
        research_context = GitHubResearcher.fetch_relevant_algorithm("GEX")

        # Step 2: Trader Agent - Select strategy based on market structure
        strategy = cls.select_strategy(market_data)

        # Step 3: Generate trader insight (reasoning)
        trader_insight = cls.get_trader_insight(ticker, market_data, strategy, research_context)

        # Step 4: Parameter Optimization (optional but recommended)
        opt_params = None
        if use_optimization:
            try:
                opt_result = ParameterOptimizer.quick_scan(ticker, strategy, days=min(days, 180))
                if "error" not in opt_result and opt_result.get("verdict") == "PASS":
                    opt_params = {
                        "tp_mult": opt_result.get("optimal_tp_multiplier", 0.5),
                        "sl_mult": opt_result.get("optimal_sl_multiplier", 1.5),
                        "t_horizon": opt_result.get("optimal_time_days", 5),
                        "ewma_span": opt_result.get("optimal_ewma_span", 20)
                    }
            except Exception as e:
                opt_params = None  # Fall back to default barriers

        # Step 5: Strategy Backtester - Triple Barrier with OOS verification
        backtest = StrategyBacktester.run_historical_backtest(ticker, strategy, days=days)

        # Step 6: Meta Labeler - ML regime detection
        meta_result = None
        if use_meta_model:
            try:
                meta = MetaLabeler()
                features = meta.build_features(ticker, lookback_days=252)
                if features is not None and len(features) >= 30:
                    X, y = meta.generate_training_labels(features, [])
                    if X is not None and len(X) >= 30 and len(np.unique(y)) > 1:
                        train_stats = meta.train_meta_model(X, y)
                        if train_stats.get("is_trained"):
                            # Get bet size for current market condition
                            current_feat = features.iloc[-1][meta._feature_names].values
                            meta_result = meta.get_bet_size(current_feat)
                            meta.save_model()
            except Exception:
                meta_result = None  # Meta-model failed, proceed without it

        # Step 7: Critic Agent - Final risk verdict
        critic_review = cls.get_critic_review(backtest, meta_result)

        # Step 8: Save to Memory
        try:
            memory_store = LocalMemoryStore()
            memory_store.log_session(
                ticker=ticker,
                market_data=market_data,
                trader_insight=trader_insight,
                backtest_result=backtest,
                critic_review=critic_review["verdict"]
            )
        except Exception:
            pass  # Memory logging failure is non-fatal

        # Assemble response
        response = {
            "ticker": ticker,
            "strategy_proposed": strategy,
            "trader_insight": trader_insight,
            "researcher_context": {
                "algorithm": research_context.get("name"),
                "source": research_context.get("source"),
                "validation": research_context.get("validation"),
                "logic": research_context.get("logic_description", "")[:200]
            },
            "optimization": opt_params,
            "backtest": backtest,
            "meta_model": meta_result,
            "critic_review": critic_review,
            "final_recommendation": cls._generate_recommendation(critic_review, strategy, market_data)
        }

        return response

    @classmethod
    def _generate_recommendation(cls, critic_review: dict, strategy: str, market_data: dict) -> dict:
        """Generate human-readable trading recommendation."""
        verdict = critic_review.get("verdict", "REJECTED")
        metrics = critic_review.get("metric_breakdown", {})

        if verdict == "APPROVED":
            action = "EXECUTE"
            summary = (
                f"{strategy.upper()} strategy APPROVED. "
                f"Win Rate: {metrics.get('win_rate', 'N/A')}, "
                f"PF: {metrics.get('profit_factor', 'N/A')}, "
                f"Max DD: {metrics.get('max_drawdown', 'N/A')}. "
                f"Sharpe: {metrics.get('sharpe_ratio', 'N/A')}"
            )
        else:
            action = "PASS"
            summary = (
                f"{strategy.upper()} strategy REJECTED. "
                f"Reason: {critic_review.get('reason', 'Unknown')}"
            )

        return {
            "action": action,
            "summary": summary,
            "key_metrics": {
                "win_rate": metrics.get("win_rate", "N/A"),
                "profit_factor": metrics.get("profit_factor", "N/A"),
                "max_drawdown": metrics.get("max_drawdown", "N/A"),
                "sharpe_ratio": metrics.get("sharpe_ratio", "N/A")
            }
        }

    @classmethod
    def run_batch_analysis(cls, tickers: list, market_data_map: dict,
                           days: int = 180) -> list:
        """
        Run agentic loop for multiple tickers.
        Used for the Global Screener to analyze top opportunities.
        """
        results = []
        for ticker in tickers:
            market_data = market_data_map.get(ticker, {})
            try:
                result = cls.run_agentic_loop(ticker, market_data, days=days)
                results.append(result)
            except Exception as e:
                results.append({
                    "ticker": ticker,
                    "error": str(e),
                    "strategy_proposed": "UNKNOWN",
                    "final_recommendation": {"action": "ERROR", "summary": str(e)}
                })

        # Sort by recommendation action (EXECUTE first) then by win rate
        results.sort(key=lambda x: (
            0 if x.get("final_recommendation", {}).get("action") == "EXECUTE" else 1,
            -float(x.get("backtest", {}).get("win_rate_percent", 0))
        ))

        return results