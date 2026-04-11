import React, { useState, useEffect } from 'react';
import { Responsive as ResponsiveGridLayout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import { Activity, LineChart, Target, CheckCircle } from 'lucide-react';
import MacroSearchTerminal from './MacroSearchTerminal';
import TradingChart from './TradingChart';
import StatArbHeatmap from './StatArbHeatmap';
import SectorHeatmap from './SectorHeatmap';
import LiveGammaExposure from './LiveGammaExposure';

interface TerminalMosaicProps {
  data: any;
  chartData: any[];
  portfolio: any;
  onBackToScanner: () => void;
}

export default function TerminalMosaic({ data, chartData, portfolio, onBackToScanner }: TerminalMosaicProps) {
  const [windowWidth, setWindowWidth] = useState(1200);

  useEffect(() => {
    setWindowWidth(window.innerWidth);
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Default Mosaic Layout (12 columns)
  const defaultLayout = [
    { i: 'macro', x: 0, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
    { i: 'portfolio', x: 0, y: 4, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'chart', x: 3, y: 0, w: 6, h: 5, minW: 4, minH: 4 },
    { i: 'statarb', x: 3, y: 5, w: 6, h: 2, minW: 4, minH: 2 },
    { i: 'agents', x: 3, y: 7, w: 6, h: 2, minW: 4, minH: 2 },
    { i: 'sector', x: 9, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
    { i: 'gex', x: 9, y: 4, w: 3, h: 5, minW: 2, minH: 3 },
  ];

  return (
    <div style={{ width: '100%', overflowX: 'hidden' }}>
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
          <div className="panel-header panel-drag-handle" style={{ cursor: 'grab', display: 'flex', justifyContent: 'space-between' }}>
             <span><Activity size={14}/> FED Macro DB</span>
             <span className="text-xs text-accent" style={{ cursor: 'pointer' }} onClick={onBackToScanner}>← SCANNER</span>
          </div>
          <div style={{ flex: 1, overflow: 'hidden' }}>
             <MacroSearchTerminal />
          </div>
        </div>

        {/* AI PAPER PORTFOLIO */}
        <div key="portfolio" className="terminal-panel" style={{ display: 'flex', flexDirection: 'column' }}>
           <div className="panel-header panel-drag-handle" style={{ cursor: 'grab' }}>
              <LineChart size={14}/> AI Paper Portfolio
           </div>
           <div className="portfolio-container" style={{ flex: 1, overflowY: 'auto' }}>
               {portfolio && (
                  <>
                    <div className="portfolio-metric">
                       <span>Cash Bal:</span>
                       <span className="text-success">${portfolio.cash_balance.toLocaleString()}</span>
                    </div>
                    <div className="trades-list">
                       {portfolio.positions.map((p: any, i: number) => (
                          <div key={i} className="trade-item">
                             <span className="trade-tkr">{p.ticker}</span>
                             <span className="trade-strat text-secondary">{p.strategy} <span className="text-accent ml-1">({p.kelly_percentage ?? 10}% Kelly)</span></span>
                          </div>
                       ))}
                    </div>
                  </>
               )}
           </div>
        </div>

        {/* TRADING CHART */}
        <div key="chart" className="terminal-panel" style={{ display: 'flex', flexDirection: 'column' }}>
           <div className="panel-header panel-drag-handle" style={{ cursor: 'grab' }}>
               Live Chart execution
           </div>
           <div className="chart-container" style={{ flex: 1 }}>
             {chartData.length > 0 ? (
                <TradingChart 
                   data={chartData} 
                   callWall={data?.market_structure?.call_wall_strike}
                   putWall={data?.market_structure?.put_wall_strike} 
                />
             ) : (
                <div className="terminal-loading">Loading Chart Data...</div>
             )}
           </div>
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

        {/* AGENT LOOP CONSENSUS */}
        <div key="agents" className="terminal-panel panel-drag-handle" style={{ cursor: 'grab', overflowY: 'auto' }}>
           <div className="agent-loop-container" style={{ border: 'none', padding: 0 }}>
              {data && (
                <>
                  <div className="agent-box border-bottom">
                     <span className="agent-title"><Target size={14} className="text-accent"/> Trader Consensus ({data.ticker})</span>
                     <p className="text-secondary text-sm">{data.agent_insights.trader_insight}</p>
                  </div>
                  <div className="agent-box">
                     <span className="agent-title"><CheckCircle size={14} className="text-success"/> AP Backtester & Critic</span>
                     <div className="flex gap-4 mt-2">
                        <div className="mini-stat">
                           <span>90D Exec:</span>
                           <span className="text-accent">{data.agent_insights.backtest.strategy_tested}</span>
                        </div>
                        <div className="mini-stat">
                           <span>Win Rate:</span>
                           <span className="text-success">{data.agent_insights.backtest.win_rate_percent}%</span>
                        </div>
                        <div className="mini-stat">
                           <span>Drawdown:</span>
                           <span className="text-danger">{data.agent_insights.backtest.max_drawdown}%</span>
                        </div>
                     </div>
                     <p className={`text-xs mt-2 ${data.paper_trade_status?.status === "OPEN" ? "text-success" : "text-danger"}`}>
                        VERDICT: {data.agent_insights.critic_review}
                     </p>
                  </div>
                </>
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
               <LiveGammaExposure />
               
               {data?.market_structure?.volatility_skew && (
               <div className="gex-stats mt-4">
                   <div className="panel-header">
                     Implied Volatility Matrix
                   </div>
                   <div className="macro-row mt-2">
                     <span>IV Skew Index</span>
                     <span className="text-primary">{data.market_structure.volatility_skew.volatility_skew_index} pts</span>
                   </div>
                   <div className="macro-row">
                     <span>Sentiment</span>
                     <span className={data.market_structure.volatility_skew.volatility_skew_index > 0 ? "text-danger" : "text-success"}>
                        {data.market_structure.volatility_skew.sentiment}
                     </span>
                   </div>
               </div>
               )}
             </>
        </div>

      </ResponsiveGridLayout>
    </div>
  );
}
