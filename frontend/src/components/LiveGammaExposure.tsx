// @ts-nocheck
import React, { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';

type Props = { ticker?: string | null };

/**
 * Local dev: WebSocket to mock 1s GEX stream.
 * Production / Vercel: poll GET /api/gex/live/{ticker} (serverless-friendly).
 * Override with VITE_WS_URL for a custom WebSocket base.
 */
export default function LiveGammaExposure({ ticker }: Props) {
  const [liveData, setLiveData] = useState<any>(null);
  const [wsStatus, setWsStatus] = useState<string>('Connecting...');

  useEffect(() => {
    const usePoll =
      import.meta.env.VITE_GEX_POLL === '1' || Boolean(import.meta.env.PROD);

    if (usePoll) {
      if (!ticker) {
        setWsStatus('OPEN A TICKER');
        setLiveData(null);
        return undefined;
      }
      let cancelled = false;
      const load = async () => {
        try {
          setWsStatus('POLLING');
          const res = await fetch(`/api/gex/live/${encodeURIComponent(ticker)}`);
          const data = await res.json();
          if (cancelled) return;
          if (data.error) {
            setWsStatus(`ERR: ${data.error}`);
            setLiveData(null);
            return;
          }
          setLiveData(data);
          setWsStatus('REST LIVE');
        } catch {
          if (!cancelled) setWsStatus('FETCH FAILED');
        }
      };
      load();
      const id = window.setInterval(load, 2000);
      return () => {
        cancelled = true;
        window.clearInterval(id);
      };
    }

    const wsBase = import.meta.env.VITE_WS_URL
      ? import.meta.env.VITE_WS_URL.replace(/\/$/, '')
      : 'ws://localhost:8005';
    const wsPath = import.meta.env.DEV ? '/ws/gex' : '/api/ws/gex';
    const wsUrl = `${wsBase}${wsPath}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setWsStatus('LIVE CONNECTED');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLiveData(data);
    };

    ws.onerror = () => {
      setWsStatus('CONNECTION FAILED');
    };

    ws.onclose = () => {
      setWsStatus('DISCONNECTED');
    };

    return () => {
      ws.close();
    };
  }, [ticker]);

  if (!ticker && (import.meta.env.PROD || import.meta.env.VITE_GEX_POLL === '1')) {
    return (
      <div className="terminal-loading">
        <Activity size={24} className="text-secondary mb-2" />
        <span className="text-xs text-secondary">Load a symbol for live chain GEX</span>
      </div>
    );
  }

  if (!liveData) {
    return (
       <div className="terminal-loading">
          <Activity size={24} className="text-secondary mb-2" />
          <span>{wsStatus}</span>
          <span className="text-xs text-secondary mt-1">
            {import.meta.env.PROD ? 'REST poll 2s' : 'Awaiting 1s WebSocket Stream'}
          </span>
       </div>
    );
  }

  return (
    <div className="gex-stats mt-2">
       <div className="flex justify-between items-center mb-3 border-bottom pb-2">
          <span className="text-xs font-mono text-secondary">
            {liveData.source === 'chain' ? 'CHAIN GEX' : 'HFT SOCKET'}: {wsStatus}
          </span>
          <span className="text-xs font-mono text-accent">
            {import.meta.env.PROD ? 'POLL: 2000ms' : 'PING: 1000ms'}
          </span>
       </div>

       <div className="macro-row">
         <span>Spot</span>
         <span className="text-accent">{Number(liveData.spot_price).toFixed(2)}</span>
       </div>
       <div className="macro-row">
         <span>Call Wall (Max Gamma Resistance)</span>
         <span className="text-success">{liveData.call_wall}</span>
       </div>
       <div className="macro-row">
         <span>Put Wall (Max Gamma Support)</span>
         <span className="text-danger">{liveData.put_wall}</span>
       </div>
       <div className="macro-row">
         <span>Dealer Micro-Tilt</span>
         <span className={liveData.dealer_tilt === 'Long Gamma' ? 'text-success' : 'text-danger'}>
            {liveData.dealer_tilt}
         </span>
       </div>
       <div className="macro-row">
         <span>Total Call GEX (Millions)</span>
         <span className="text-success">${liveData.total_call_gex_m}M</span>
       </div>
       <div className="macro-row">
         <span>Total Put GEX (Millions)</span>
         <span className="text-danger">${liveData.total_put_gex_m}M</span>
       </div>

       <div className="mt-4">
          <div className="text-xs text-secondary mb-1">GEX Order Book Depth</div>
          {(liveData.strikes || []).slice(8, 13).map((strike: any, i: number) => (
             <div key={i} className="flex justify-between items-center text-xs font-mono mt-1">
                <span className={strike.strike === liveData.call_wall ? 'text-success' : strike.strike === liveData.put_wall ? 'text-danger' : ''}>
                   {strike.strike}
                </span>
                <div style={{ flex: 1, margin: '0 8px', display: 'flex', border: '1px solid #333' }}>
                   <div style={{
                       width: '50%',
                       display: 'flex',
                       justifyContent: 'flex-end',
                       borderRight: '1px solid #444'
                   }}>
                      <div style={{
                          backgroundColor: 'rgba(239, 68, 68, 0.4)',
                          width: `${Math.min(100, Math.abs(strike.put_gex) / 2)}%`,
                          height: '10px'
                      }}></div>
                   </div>
                   <div style={{ width: '50%', display: 'flex' }}>
                      <div style={{
                          backgroundColor: 'rgba(34, 197, 94, 0.4)',
                          width: `${Math.min(100, strike.call_gex / 2)}%`,
                          height: '10px'
                      }}></div>
                   </div>
                </div>
                <span>{Number(strike.net_gex).toFixed(1)}M</span>
             </div>
          ))}
       </div>
    </div>
  );
}
