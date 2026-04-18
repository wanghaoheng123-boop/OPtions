// @ts-nocheck
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Search, LayoutDashboard } from 'lucide-react';
import GlobalDiscoveryFeed from './components/GlobalDiscoveryFeed';
import TerminalMosaic from './components/TerminalMosaic';
import CommandPalette from './components/CommandPalette';
import './index.css';

function axiosErrMessage(err: any): string {
  const d = err?.response?.data?.detail ?? err?.response?.data?.message;
  if (typeof d === 'string') return d;
  if (d != null) return JSON.stringify(d);
  return err?.message || 'Request failed';
}

function App() {
  const [ticker, setTicker] = useState('');
  const [viewMode, setViewMode] = useState<'discovery' | 'terminal'>('discovery');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [chartFetchError, setChartFetchError] = useState<string | null>(null);
  const [chartRenderError, setChartRenderError] = useState<string | null>(null);

  const chartPanelError = chartFetchError || chartRenderError;

  const onChartRenderError = useCallback((msg: string) => {
    setChartRenderError(msg || 'Chart rendering failed');
  }, []);

  const fetchAnalysis = async (targetTicker: string) => {
    setLoading(true);
    setViewMode('terminal');
    setAnalyzeError(null);
    setPortfolioError(null);
    setChartFetchError(null);
    setChartRenderError(null);

    const settled = await Promise.allSettled([
      axios.post('/api/analyze', { ticker: targetTicker }),
      axios.get(`/api/chart/${targetTicker}`),
      axios.get('/api/portfolio'),
    ]);

    const [anRes, chRes, poRes] = settled;

    if (anRes.status === 'fulfilled') {
      setData(anRes.value.data);
      setAnalyzeError(null);
    } else {
      setData(null);
      setAnalyzeError(axiosErrMessage(anRes.reason));
    }

    if (chRes.status === 'fulfilled') {
      const series = chRes.value.data?.data;
      if (!Array.isArray(series) || series.length === 0) {
        setChartData([]);
        setChartFetchError(
          chRes.value.data?.detail ||
            'No OHLC data returned (empty series or ticker not found).'
        );
      } else {
        setChartData(series);
        setChartFetchError(null);
      }
    } else {
      setChartData([]);
      setChartFetchError(axiosErrMessage(chRes.reason));
    }

    if (poRes.status === 'fulfilled') {
      setPortfolio(poRes.value.data);
      setPortfolioError(null);
    } else {
      setPortfolioError(axiosErrMessage(poRes.reason));
    }

    setLoading(false);
  };

  // Initial load: Only load portfolio and discovery mode by default
  useEffect(() => {
    axios
      .get('/api/portfolio')
      .then((res) => setPortfolio(res.data))
      .catch((err) => {
        setPortfolioError(err?.message || 'Failed to load portfolio');
      });
  }, []);

  const handleSearch = () => {
     if (ticker.trim()) fetchAnalysis(ticker.toUpperCase());
  };

  const terminalIssueLines = [
    analyzeError && `Analyze: ${analyzeError}`,
    chartPanelError && `Chart: ${chartPanelError}`,
    portfolioError && `Portfolio: ${portfolioError}`,
  ].filter(Boolean);

  return (
    <div className="terminal-body">
      <CommandPalette
        setViewMode={setViewMode}
        onRunSearch={() => ticker.trim() && fetchAnalysis(ticker.toUpperCase())}
        onClearTerminalErrors={() => {
          setAnalyzeError(null);
          setPortfolioError(null);
          setChartFetchError(null);
          setChartRenderError(null);
        }}
      />
      {terminalIssueLines.length > 0 && viewMode === 'terminal' && (
        <div className="terminal-error-banner" role="alert">
          <strong>Data issues</strong>
          <ul className="terminal-error-banner__list">
            {terminalIssueLines.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </div>
      )}
      <nav className="terminal-nav">
        <div className="nav-brand">
          <LayoutDashboard size={20} className="text-accent" />
          <span>Options research terminal</span>
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
            analyzeError={analyzeError}
            portfolioError={portfolioError}
            chartError={chartPanelError}
            onChartRenderError={onChartRenderError}
            onBackToScanner={() => {
              setViewMode('discovery');
              setAnalyzeError(null);
              setPortfolioError(null);
              setChartFetchError(null);
              setChartRenderError(null);
            }} 
         />
      )}
    </div>
  );
}

export default App;
