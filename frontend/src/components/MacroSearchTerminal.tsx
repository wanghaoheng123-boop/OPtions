// @ts-nocheck
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, BarChart3, AlertTriangle } from 'lucide-react';
import TradingChart from './TradingChart';
import { extractApiErrorMessage } from '../lib/apiError';

export default function MacroSearchTerminal() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSeries, setSelectedSeries] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [errorMsg, setErrorMsg] = useState('');

  const searchFred = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const res = await axios.get(`/api/macro/search?query=${encodeURIComponent(query)}`);
      if (res.data.results?.error) {
         setErrorMsg(res.data.results.message);
         setResults([]);
      } else {
         setResults(res.data.results || []);
      }
    } catch (err: any) {
      console.error(err);
      setErrorMsg(extractApiErrorMessage(err, 'Failed to query macro backend'));
    } finally {
      setLoading(false);
    }
  };

  const loadSeries = async (series: any) => {
    setSelectedSeries(series);
    setChartData([]);
    setErrorMsg('');
    try {
      const res = await axios.get(`/api/macro/series/${series.id}`);
      if (res.data.data?.error) {
          setErrorMsg(res.data.data.message);
      } else {
          const raw = res.data.data || [];
          const asOhlc = raw.map((pt: any) => {
            const v = Number(pt?.value);
            return {
              time: pt?.time,
              open: v,
              high: v,
              low: v,
              close: v,
            };
          }).filter((pt: any) => pt.time && Number.isFinite(pt.close));
          setChartData(asOhlc);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(extractApiErrorMessage(err, 'Failed to load macro series'));
    }
  };

  return (
    <div className="macro-search-panel">
      {errorMsg && (
        <div className="bg-danger text-xs p-2 mb-2 rounded border border-danger flex gap-2">
           <AlertTriangle size={14}/> {errorMsg}
        </div>
      )}
      
      {!selectedSeries ? (
        <>
          <div className="nav-search" style={{ marginBottom: '10px' }}>
            <input 
              type="text" 
              value={query} 
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchFred()}
              placeholder="Search FED Data (e.g. GDP)..." 
              className="terminal-input"
              style={{ width: '100%' }}
            />
            <button onClick={searchFred} className="terminal-btn-primary">
               {loading ? '...' : <Search size={14} />}
            </button>
          </div>

          <div className="fed-results" style={{ overflowY: 'auto', maxHeight: '400px' }}>
            {results.map((r) => (
              <div 
                key={r.id} 
                className="trade-item cursor-pointer hover:bg-dark p-2"
                onClick={() => loadSeries(r)}
                style={{ cursor: 'pointer', borderBottom: '1px solid #1e1e1e' }}
              >
                <div className="flex flex-col">
                  <span className="text-sm font-semibold">{r.title}</span>
                  <span className="text-secondary text-xs">{r.id} | {r.frequency}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="fed-chart-view flex flex-col h-full">
           <div className="flex justify-between items-center mb-2">
             <div className="flex flex-col">
                <span className="text-sm font-bold text-accent">{selectedSeries.id}</span>
                <span className="text-xs text-secondary">{selectedSeries.title}</span>
             </div>
             <button onClick={() => setSelectedSeries(null)} className="terminal-btn-primary text-xs">
                Back
             </button>
           </div>
           
           <div style={{ height: '250px', width: '100%' }}>
             {chartData.length > 0 ? (
                <TradingChart data={chartData} />
             ) : (
                <div className="terminal-loading">Loading Historic FED Data...</div>
             )}
           </div>
        </div>
      )}
    </div>
  );
}
