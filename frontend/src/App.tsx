// @ts-nocheck
import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Search, LayoutDashboard } from 'lucide-react';
import GlobalDiscoveryFeed from './components/GlobalDiscoveryFeed';
import TerminalMosaic from './components/TerminalMosaic';
import CommandPalette from './components/CommandPalette';
import './index.css';

function axiosErrMessage(err: any): string {
  if (!err?.response) {
    const msg = err?.message || '';
    if (msg.includes('Network Error') || err?.code === 'ERR_NETWORK') {
      return 'Cannot reach API. For local dev start the backend on port 8005 (see README).';
    }
    return msg || 'Request failed (no response)';
  }
  const d = err?.response?.data?.detail ?? err?.response?.data?.message;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return JSON.stringify(d);
  if (d != null) return JSON.stringify(d);
  return err?.message || `Request failed with status code ${err.response?.status}`;
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
  const requestSeqRef = useRef(0);
  const activeControllerRef = useRef<AbortController | null>(null);

  const chartPanelError = chartFetchError || chartRenderError;

  const onChartRenderError = useCallback((msg: string) => {
    setChartRenderError(msg || 'Chart rendering failed');
  }, []);

  const fetchAnalysis = async (targetTicker: string) => {
    requestSeqRef.current += 1;
    const requestSeq = requestSeqRef.current;
    if (activeControllerRef.current) {
      activeControllerRef.current.abort();
    }
    const controller = new AbortController();
    activeControllerRef.current = controller;

    setLoading(true);
    setViewMode('terminal');
    setAnalyzeError(null);
    setPortfolioError(null);
    setChartFetchError(null);
    setChartRenderError(null);

    const settled = await Promise.allSettled([
      axios.post('/api/analyze', { ticker: targetTicker }, { signal: controller.signal, timeout: 30000 }),
      axios.get(`/api/chart/${targetTicker}`, { signal: controller.signal, timeout: 30000 }),
      axios.get('/api/portfolio', { signal: controller.signal, timeout: 30000 }),
    ]);

    if (requestSeq !== requestSeqRef.current) return;

    const [anRes, chRes, poRes] = settled;

    if (anRes.status === 'fulfilled') {
      setData(anRes.value.data);
      setAnalyzeError(null);
    } else {
      if (anRes.reason?.code !== 'ERR_CANCELED') {
        setData(null);
        setAnalyzeError(axiosErrMessage(anRes.reason));
      }
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
      if (chRes.reason?.code !== 'ERR_CANCELED') {
        setChartData([]);
        setChartFetchError(axiosErrMessage(chRes.reason));
      }
    }

    if (poRes.status === 'fulfilled') {
      setPortfolio(poRes.value.data);
      setPortfolioError(null);
    } else {
      if (poRes.reason?.code !== 'ERR_CANCELED') {
        setPortfolioError(axiosErrMessage(poRes.reason));
      }
    }

    if (requestSeq === requestSeqRef.current) {
      setLoading(false);
      activeControllerRef.current = null;
    }
  };

  // Initial load: Only load portfolio and discovery mode by default
  useEffect(() => {
    const controller = new AbortController();
    axios
      .get('/api/portfolio', { signal: controller.signal, timeout: 30000 })
      .then((res) => setPortfolio(res.data))
      .catch((err) => {
        if (err?.code !== 'ERR_CANCELED') {
          setPortfolioError(axiosErrMessage(err));
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    return () => {
      if (activeControllerRef.current) {
        activeControllerRef.current.abort();
      }
    };
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
    <div className="terminal-body" data-testid="app-shell">
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
        <div className="terminal-error-banner" role="alert" data-testid="terminal-error-banner">
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
          <button
            type="button"
            onClick={handleSearch}
            disabled={loading}
            className="terminal-btn-primary"
            aria-label="Run ticker search"
          >
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
