// @ts-nocheck
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Target, Activity, CheckCircle, Search, LayoutDashboard, LineChart } from 'lucide-react';
import TradingChart from './components/TradingChart';
import MacroSearchTerminal from './components/MacroSearchTerminal';
import StatArbHeatmap from './components/StatArbHeatmap';
import GlobalDiscoveryFeed from './components/GlobalDiscoveryFeed';
import TerminalMosaic from './components/TerminalMosaic';
import './index.css';

function App() {
  const [ticker, setTicker] = useState('');
  const [activeTicker, setActiveTicker] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'discovery' | 'terminal'>('discovery');
  console.log("FORCE CACHE RESET. INITIAL MODE:", viewMode);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<any>(null);

  const fetchAnalysis = async (targetTicker: string) => {
    setLoading(true);
    setViewMode('terminal');
    setActiveTicker(targetTicker);
    try {
      // Parallel requests for dense terminal loading
      const [analysisRes, chartRes, portRes] = await Promise.all([
         axios.post('/api/analyze', { ticker: targetTicker }),
         axios.get(`/api/chart/${targetTicker}`),
         axios.get('/api/portfolio')
      ]);
      
      setData(analysisRes.data);
      setChartData(chartRes.data.data);
      setPortfolio(portRes.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load: Only load portfolio and discovery mode by default
  useEffect(() => {
    axios.get('/api/portfolio').then(res => setPortfolio(res.data));
  }, []);

  const handleSearch = () => {
     if (ticker.trim()) fetchAnalysis(ticker.toUpperCase());
  };

  return (
    <div className="terminal-body">
      {/* Top Navbar */}
      <nav className="terminal-nav">
        <div className="nav-brand">
          <LayoutDashboard size={20} className="text-accent" />
          <span>Bloomberg / Polymarket Proxy V2</span>
        </div>
        <div className="nav-search">
          <input 
            type="text" 
            value={ticker} 
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search Specific Ticker..." 
            className="terminal-input"
          />
          <button onClick={handleSearch} disabled={loading} className="terminal-btn-primary">
            {loading ? 'F...' : <Search size={14} />}
          </button>
        </div>
      </nav>

      {/* Dynamic View Mode Router */}
      {viewMode === 'discovery' ? (
         <div style={{ marginTop: '24px' }}>
            <GlobalDiscoveryFeed onSelectTicker={(t) => {
               setTicker(t);
               fetchAnalysis(t);
            }} />
         </div>
      ) : (
         <TerminalMosaic 
            data={data} 
            chartData={chartData} 
            portfolio={portfolio} 
            onBackToScanner={() => setViewMode('discovery')} 
         />
      )}
    </div>
  );
}

export default App;
