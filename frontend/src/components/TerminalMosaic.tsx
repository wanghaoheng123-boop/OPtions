// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { Responsive as ResponsiveGridLayout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import { Activity, LineChart, Target, CheckCircle, Brain, TrendingUp } from 'lucide-react';
import MacroSearchTerminal from './MacroSearchTerminal';
import TradingChart from './TradingChart';
import StatArbHeatmap from './StatArbHeatmap';
import SectorHeatmap from './SectorHeatmap';
import LiveGammaExposure from './LiveGammaExposure';
import MethodologyDrawer from './MethodologyDrawer';

interface TerminalMosaicProps {
  data: any;
  chartData: any[];
  portfolio: any;
  analyzeError?: string | null;
  portfolioError?: string | null;
  chartError?: string | null;
  onChartRenderError?: (msg: string) => void;
  onBackToScanner: () => void;
}

export default function TerminalMosaic({
  data,
  chartData,
  portfolio,
  analyzeError,
  portfolioError,
  chartError,
  onChartRenderError,
  onBackToScanner,
}: TerminalMosaicProps) {
  const [windowWidth, setWindowWidth] = useState(1200);

  useEffect(() => {
    setWindowWidth(window.innerWidth);
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Default Mosaic Layout (12 columns) — expanded for new panels
  const defaultLayout = [
    { i: 'macro', x: 0, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
    { i: 'portfolio', x: 0, y: 4, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'chart', x: 3, y: 0, w: 6, h: 5, minW: 4, minH: 4 },
    { i: 'hmm', x: 9, y: 0, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'meta', x: 9, y: 3, w: 3, h: 2, minW: 2, minH: 2 },
    { i: 'statarb', x: 3, y: 5, w: 6, h: 2, minW: 4, minH: 2 },
    { i: 'agents', x: 3, y: 7, w: 6, h: 2, minW: 4, minH: 2 },
    { i: 'sector', x: 0, y: 7, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'gex', x: 9, y: 5, w: 3, h: 5, minW: 2, minH: 3 },
  ];

  // Extract data safely with fallbacks
  const agentInsights = data?.agent_insights || data || {};
  const backtest = agentInsights?.backtest || {};
  const marketStructure = data?.market_structure || {};
  const criticReview = agentInsights?.critic_review || {};
  const metaModel = agentInsights?.meta_model || {};
  const researchCtx = agentInsights?.researcher_context || {};
  const optimization = agentInsights?.optimization || {};

  // Color helper
  const pctColor = (val) => {
    if (typeof val !== 'number') return 'text-secondary';
    if (val >= 75) return 'text-success';
    if (val >= 50) return 'text-warning';
    return 'text-danger';
  };

  const verdictColor = (v) => {
    if (v === 'APPROVED') return 'text-success';
    if (v === 'REJECTED') return 'text-danger';
    return 'text-secondary';
  };

  return (
    <div className="terminal-mosaic-root">
      <div className="terminal-zone-legend" aria-hidden="true">
        <span className="terminal-zone-legend__label">Research</span>
        <span className="text-secondary">macro · stat-arb · sector</span>
        <span className="terminal-zone-legend__sep">|</span>
        <span className="terminal-zone-legend__label">Market</span>
        <span className="text-secondary">chart · GEX</span>
        <span className="terminal-zone-legend__sep">|</span>
        <span className="terminal-zone-legend__label">Risk / models</span>
        <span className="text-secondary">portfolio · HMM · meta · agents</span>
      </div>
      {analyzeError && (
        <div className="terminal-analyze-strip" role="status">
          <strong>Analyze pipeline:</strong> {analyzeError} — other panels (e.g. OHLC chart) may still load
          independently.
        </div>
      )}
      {portfolioError && (
        <div className="terminal-portfolio-strip" role="status">
          <strong>Paper portfolio:</strong> {portfolioError}
        </div>
      )}
      <ResponsiveGridLayout
        className="layout"
        width={windowWidth}
        layouts={{ lg: defaultLayout }}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={80}
        draggableHandle=".panel-drag-handle"
        margin={[16, 16]}
      >

        {/* MACRO DATABASE */}
        <div key="macro" className="terminal-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <div
            className="panel-header panel-drag-handle panel-header--split"
            style={{ cursor: 'grab' }}
          >
            <span>
              <Activity size={14} /> FED Macro DB
            </span>
            <span className="panel-header__actions">
              <MethodologyDrawer panelId="macro" />
              <span className="text-xs text-accent panel-header__link" onClick={onBackToScanner}>
                ← SCANNER
              </span>
            </span>
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
             <MacroSearchTerminal />
          </div>
        </div>

        {/* AI PAPER PORTFOLIO */}
        <div key="portfolio" className="terminal-panel" style={{ display: 'flex', flexDirection: 'column' }}>
           <div className="panel-header panel-drag-handle panel-header--split" style={{ cursor: 'grab' }}>
              <span>
                <LineChart size={14} /> AI Paper Portfolio
              </span>
              <MethodologyDrawer panelId="portfolio" />
           </div>
           <div className="portfolio-container" style={{ flex: 1, overflowY: 'auto' }}>
               {portfolio && (
                  <>
                    <div className="portfolio-metric">
                       <span>Cash Bal:</span>
                       <span className="text-success">${(portfolio.cash_balance || 0).toLocaleString()}</span>
                    </div>
                    <div className="portfolio-metric">
                       <span>Total Return:</span>
                       <span className={portfolio.total_return >= 0 ? 'text-success' : 'text-danger'}>
                          {((portfolio.total_return || 0) * 100).toFixed(2)}%
                       </span>
                    </div>
                    <div className="portfolio-metric">
                       <span>Win Rate:</span>
                       <span className="text-accent">{((portfolio.win_rate || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="portfolio-metric">
                       <span>Kelly Avg:</span>
                       <span className="text-warning">{((portfolio.average_kelly_sizing || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="trades-list">
                       {(portfolio.positions || []).map((p: any, i: number) => (
                          <div key={i} className="trade-item">
                             <span className="trade-tkr">{p.ticker}</span>
                             <span className="trade-strat text-secondary">{p.strategy} <span className="text-accent ml-1">({((p.kelly_percentage || 0.1) * 100).toFixed(0)}%)</span></span>
                          </div>
                       ))}
                    </div>
                  </>
               )}
           </div>
        </div>

        {/* TRADING CHART */}
        <div key="chart" className="terminal-panel" style={{ display: 'flex', flexDirection: 'column' }}>
           <div className="panel-header panel-drag-handle panel-header--split" style={{ cursor: 'grab' }}>
               <span>Live Chart — {data?.ticker || '—'}</span>
               <MethodologyDrawer panelId="chart" />
           </div>
           <div className="chart-container" style={{ flex: 1 }}>
             {chartData.length > 0 ? (
                <TradingChart
                   data={chartData}
                   callWall={marketStructure?.call_wall_strike}
                   putWall={marketStructure?.put_wall_strike}
                   onChartError={onChartRenderError}
                />
             ) : chartError || (analyzeError && !chartData.length) ? (
                <div className="terminal-empty-state terminal-empty-state--error">
                  <p className="terminal-empty-state__title">Chart unavailable</p>
                  <p className="terminal-empty-state__body">
                    {chartError || analyzeError}
                  </p>
                </div>
             ) : (
                <div className="terminal-empty-state">
                  <p className="terminal-empty-state__title">No chart series yet</p>
                  <p className="terminal-empty-state__body">Run a ticker search to load daily OHLC from the chart API.</p>
                </div>
             )}
           </div>
        </div>

        {/* HMM REGIME DETECTION */}
        <div key="hmm" className="terminal-panel panel-drag-handle" style={{ cursor: 'grab', overflowY: 'auto' }}>
           <div className="panel-header panel-header--split">
             <span>
               <TrendingUp size={14} className="text-accent" /> HMM Regime
             </span>
             <MethodologyDrawer panelId="hmm_regime" />
           </div>
           {data?.agent_insights?.hmm_regime ? (
             <>
               <div className="regime-label" style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                 <span className="text-accent">{data.agent_insights.hmm_regime.regime_label}</span>
               </div>
               <div className="flex gap-2 mt-2" style={{ gap: '8px', flexWrap: 'wrap' }}>
                 <div className="mini-stat">
                    <span>Strategy:</span>
                    <span className="text-accent">{data.agent_insights.hmm_regime.recommended_strategy}</span>
                 </div>
                 <div className="mini-stat">
                    <span>Confidence:</span>
                    <span className={data.agent_insights.hmm_regime.confidence > 0.6 ? 'text-success' : 'text-warning'}>
                       {(data.agent_insights.hmm_regime.confidence * 100).toFixed(0)}%
                    </span>
                 </div>
               </div>
               <div className="mini-stat mt-1">
                  <span>Vol Regime:</span>
                  <span>{data.agent_insights.hmm_regime.regime_characteristics?.volatility}</span>
               </div>
               <div className="mini-stat">
                  <span>VIX Proxy:</span>
                  <span>{data.agent_insights.hmm_regime.regime_characteristics?.vix_proxy?.toFixed(2)}</span>
               </div>
             </>
           ) : (
             <div className="text-secondary text-xs mt-2">
               HMM regime computed from 4-state Gaussian HMM on returns, vol, VIX proxy
             </div>
           )}
        </div>

        {/* META-MODEL VERDICT */}
        <div key="meta" className="terminal-panel panel-drag-handle" style={{ cursor: 'grab', overflowY: 'auto' }}>
           <div className="panel-header panel-header--split">
             <span>
               <Brain size={14} className="text-accent" /> Meta-Model ML
             </span>
             <MethodologyDrawer panelId="analyze" />
           </div>
           {metaModel && Object.keys(metaModel).length > 0 ? (
             <>
               <div className="meta-verdict" style={{ marginTop: '4px' }}>
                 <span className={metaModel.verdict === 'APPROVE' ? 'text-success' : 'text-danger'}>
                   {metaModel.verdict}
                 </span>
                 <span className="text-secondary ml-2">({((metaModel.bet_size || 1) * 100).toFixed(0)}% sizing)</span>
               </div>
               <div className="mini-stat mt-2">
                  <span>Confidence:</span>
                  <span className={
                    metaModel.confidence === 'high' ? 'text-success' :
                    metaModel.confidence === 'medium' ? 'text-warning' : 'text-danger'
                  }>{metaModel.confidence}</span>
               </div>
               {metaModel.reason && (
                 <div className="text-xs text-secondary mt-1" style={{ fontSize: '0.7rem' }}>
                   {metaModel.reason.substring(0, 80)}...
                 </div>
               )}
             </>
           ) : (
             <div className="text-secondary text-xs mt-2">
               Random Forest meta-labeler: regime shift detection
             </div>
           )}
        </div>

        {/* STATISTICAL ARBITRAGE */}
        <div key="statarb" className="terminal-panel" style={{ display: 'flex', flexDirection: 'column' }}>
           <div className="panel-header panel-drag-handle" style={{ cursor: 'grab' }}>
               Statistical Arbitrage Z-Score Matrix
           </div>
           <div style={{ flex: 1, overflowY: 'auto' }}>
               <StatArbHeatmap />
           </div>
        </div>

        {/* AGENT LOOP CONSENSUS — FULL METRICS */}
        <div key="agents" className="terminal-panel panel-drag-handle" style={{ cursor: 'grab', overflowY: 'auto' }}>
           <div className="agent-loop-container" style={{ border: 'none', padding: 0 }}>
              {agentInsights && Object.keys(agentInsights).length > 0 ? (
                <>
                  <div className="agent-box border-bottom">
                     <span className="agent-title">
                       <Target size={14} className="text-accent"/>
                       Trader: {agentInsights.strategy_proposed || 'N/A'}
                     </span>
                     <p className="text-secondary text-sm">{agentInsights.trader_insight}</p>
                     {researchCtx.name && (
                       <p className="text-xs text-accent mt-1">
                         Algo: {researchCtx.name}
                       </p>
                     )}
                  </div>

                  <div className="agent-box">
                     <span className="agent-title">
                       <CheckCircle size={14} className="text-success"/>
                       Backtester + Critic
                     </span>
                     <div className="flex gap-3 mt-2" style={{ gap: '12px', flexWrap: 'wrap' }}>
                        <div className="mini-stat">
                           <span>WR:</span>
                           <span className={pctColor(backtest.win_rate_percent)}>
                             {backtest.win_rate_percent?.toFixed(1) || 'N/A'}%
                           </span>
                        </div>
                        <div className="mini-stat">
                           <span>PF:</span>
                           <span className={backtest.profit_factor >= 1.2 ? 'text-success' : 'text-danger'}>
                             {backtest.profit_factor?.toFixed(2) || 'N/A'}
                           </span>
                        </div>
                        <div className="mini-stat">
                           <span>DD:</span>
                           <span className={backtest.max_drawdown < 20 ? 'text-success' : 'text-danger'}>
                             {backtest.max_drawdown?.toFixed(1) || 'N/A'}%
                           </span>
                        </div>
                        <div className="mini-stat">
                           <span>Sharpe:</span>
                           <span>{backtest.sharpe_ratio?.toFixed(2) || 'N/A'}</span>
                        </div>
                        <div className="mini-stat">
                           <span>Sortino:</span>
                           <span>{backtest.sortino_ratio?.toFixed(2) || 'N/A'}</span>
                        </div>
                        <div className="mini-stat">
                           <span>Calmar:</span>
                           <span>{backtest.calmar_ratio?.toFixed(2) || 'N/A'}</span>
                        </div>
                        <div className="mini-stat">
                           <span>Trades:</span>
                           <span>{backtest.num_trades || 0}</span>
                        </div>
                        {backtest.barrier_hits && (
                          <div className="mini-stat">
                             <span>PT/SL/T:</span>
                             <span className="text-secondary">
                               {backtest.barrier_hits.pt || 0}/{backtest.barrier_hits.sl || 0}/{backtest.barrier_hits.time || 0}
                             </span>
                          </div>
                        )}
                     </div>

                     {/* Optimization params */}
                     {optimization && Object.keys(optimization).length > 0 && (
                       <div className="flex gap-2 mt-1" style={{ gap: '8px' }}>
                         <span className="text-xs text-accent">Opt:</span>
                         <span className="text-xs text-secondary">
                           TP={optimization.tp_mult?.toFixed(1)}, SL={optimization.sl_mult?.toFixed(1)},
                           T={optimization.t_horizon}d, EWMA={optimization.ewma_span}
                         </span>
                       </div>
                     )}

                     {/* Critic verdict */}
                     {criticReview.verdict && (
                       <p className={`text-xs mt-2 ${criticReview.verdict === 'APPROVED' ? 'text-success' : 'text-danger'}`}>
                          VERDICT: {criticReview.verdict} — {criticReview.reason?.substring(0, 100)}
                       </p>
                     )}
                  </div>
                </>
              ) : (
                <div className="text-secondary text-xs">Agent insights loading...</div>
              )}
           </div>
        </div>

        {/* SECTOR HEATMAP */}
        <div key="sector" className="terminal-panel" style={{ display: 'flex', flexDirection: 'column' }}>
           <div className="panel-header panel-drag-handle" style={{ cursor: 'grab' }}>
             Global Sector Heatmap
           </div>
           <div style={{ flex: 1 }}>
              <SectorHeatmap />
           </div>
        </div>

        {/* GEX & IV MATRIX */}
        <div key="gex" className="terminal-panel panel-drag-handle" style={{ cursor: 'grab', overflowY: 'auto' }}>
             <>
               <div className="panel-header">
                 High-Frequency Gamma Exposure (1s Tick)
               </div>
               <LiveGammaExposure ticker={data?.ticker} />

               {marketStructure?.volatility_skew && (
               <div className="gex-stats mt-4">
                   <div className="panel-header">
                     Implied Volatility Matrix
                   </div>
                   <div className="macro-row mt-2">
                     <span>IV Skew Index</span>
                     <span className="text-primary">{marketStructure.volatility_skew.volatility_skew_index} pts</span>
                   </div>
                   <div className="macro-row">
                     <span>Sentiment</span>
                     <span className={marketStructure.volatility_skew.volatility_skew_index > 0 ? "text-danger" : "text-success"}>
                        {marketStructure.volatility_skew.sentiment}
                     </span>
                   </div>
               </div>
               )}

               {/* IV Rank & Percentile */}
               {marketStructure?.iv_rank && (
               <div className="gex-stats mt-2">
                   <div className="panel-header">IV Rank / Percentile</div>
                   <div className="macro-row mt-2">
                     <span>IV Rank</span>
                     <span className={marketStructure.iv_rank.iv_rank > 50 ? "text-danger" : "text-success"}>
                       {marketStructure.iv_rank.iv_rank?.toFixed(1)}%
                     </span>
                   </div>
                   <div className="macro-row">
                     <span>IV Verdict</span>
                     <span className={
                       marketStructure.iv_rank.verdict === 'SELL_PREMIUM' ? 'text-danger' :
                       marketStructure.iv_rank.verdict === 'BUY_PREMIUM' ? 'text-success' : 'text-secondary'
                     }>{marketStructure.iv_rank.verdict}</span>
                   </div>
                   {marketStructure.iv_percentile && (
                     <>
                     <div className="macro-row">
                       <span>IV Percentile</span>
                       <span>{marketStructure.iv_percentile.iv_percentile?.toFixed(1)}%</span>
                     </div>
                     <div className="macro-row">
                       <span>Pct Verdict</span>
                       <span className={
                         marketStructure.iv_percentile.verdict === 'SELL_PREMIUM' ? 'text-danger' :
                         marketStructure.iv_percentile.verdict === 'BUY_PREMIUM' ? 'text-success' : 'text-secondary'
                       }>{marketStructure.iv_percentile.verdict}</span>
                     </div>
                     </>
                   )}
               </div>
               )}

               {/* Full Volatility Analysis */}
               {marketStructure?.full_volatility_analysis && (
               <div className="gex-stats mt-2">
                   <div className="panel-header">Aggregate Verdict</div>
                   <div className="macro-row mt-2">
                     <span>Action:</span>
                     <span className="text-accent">{marketStructure.full_volatility_analysis.aggregate_verdict}</span>
                   </div>
               </div>
               )}
             </>
        </div>

      </ResponsiveGridLayout>
    </div>
  );
}