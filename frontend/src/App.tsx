// @ts-nocheck
import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { Search, LayoutDashboard } from 'lucide-react';
import GlobalDiscoveryFeed from './components/GlobalDiscoveryFeed';
import TerminalMosaic from './components/TerminalMosaic';
import CommandPalette from './components/CommandPalette';
import { extractApiErrorMessage } from './lib/apiError';
import './index.css';

function axiosErrMessage(err: any): string {
  return extractApiErrorMessage(err, 'Request failed');
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
  const [dataHealth, setDataHealth] = useState({
    analyze: { status: 'idle', ts: null as string | null },
    chart: { status: 'idle', ts: null as string | null },
    portfolio: { status: 'idle', ts: null as string | null },
  });
  const requestSeqRef = useRef(0);
  const activeControllerRef = useRef<AbortController | null>(null);

  const chartPanelError = chartFetchError || chartRenderError;
  const stampNow = () => new Date().toISOString();
  const markHealth = (key: 'analyze' | 'chart' | 'portfolio', status: 'ok' | 'error' | 'loading' | 'idle') => {
    setDataHealth((prev) => ({ ...prev, [key]: { status, ts: stampNow() } }));
  };

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
    markHealth('analyze', 'loading');
    markHealth('chart', 'loading');
    markHealth('portfolio', 'loading');

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
      markHealth('analyze', 'ok');
    } else {
      if (anRes.reason?.code !== 'ERR_CANCELED') {
        setData(null);
        setAnalyzeError(axiosErrMessage(anRes.reason));
        markHealth('analyze', 'error');
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
        markHealth('chart', 'ok');
      }
    } else {
      if (chRes.reason?.code !== 'ERR_CANCELED') {
        setChartData([]);
        setChartFetchError(axiosErrMessage(chRes.reason));
        markHealth('chart', 'error');
      }
    }

    if (poRes.status === 'fulfilled') {
      setPortfolio(poRes.value.data);
      setPortfolioError(null);
      markHealth('portfolio', 'ok');
    } else {
      if (poRes.reason?.code !== 'ERR_CANCELED') {
        setPortfolioError(axiosErrMessage(poRes.reason));
        markHealth('portfolio', 'error');
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
      .then((res) => {
        setPortfolio(res.data);
        markHealth('portfolio', 'ok');
      })
      .catch((err) => {
        if (err?.code !== 'ERR_CANCELED') {
          setPortfolioError(axiosErrMessage(err));
          markHealth('portfolio', 'error');
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
      <div className="data-health-strip" role="status" aria-live="polite">
        <span className="data-health-strip__item">
          Analyze:
          <strong className={`data-health-strip__status data-health-strip__status--${dataHealth.analyze.status}`}>
            {dataHealth.analyze.status}
          </strong>
        </span>
        <span className="data-health-strip__item">
          Chart:
          <strong className={`data-health-strip__status data-health-strip__status--${dataHealth.chart.status}`}>
            {dataHealth.chart.status}
          </strong>
        </span>
        <span className="data-health-strip__item">
          Portfolio:
          <strong className={`data-health-strip__status data-health-strip__status--${dataHealth.portfolio.status}`}>
            {dataHealth.portfolio.status}
          </strong>
        </span>
        <span className="data-health-strip__ts">
          Last update: {(dataHealth.portfolio.ts || dataHealth.chart.ts || dataHealth.analyze.ts || 'n/a').replace('T', ' ').slice(0, 19)}
        </span>
      </div>

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
