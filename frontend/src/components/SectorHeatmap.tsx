// @ts-nocheck
import { useEffect, useState } from 'react';
import axios from 'axios';
import { extractApiErrorMessage } from '../lib/apiError';

interface SectorData {
  id: string;
  ticker: string;
  performance: number;
}

export default function SectorHeatmap() {
  const [sectors, setSectors] = useState<SectorData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    axios
      .get('/api/heatmap')
      .then((res) => {
        if (Array.isArray(res.data)) {
          setSectors(res.data);
          setError(null);
          return;
        }
        setSectors([]);
        setError('Heatmap response shape is invalid.');
      })
      .catch((err) => {
        setSectors([]);
        setError(extractApiErrorMessage(err, 'Heatmap request failed'));
      });
  }, []);

  if (error) {
    return <div className="terminal-loading">{error}</div>;
  }

  return (
    <div className="heatmap-grid">
      {sectors.map((sector) => {
        const isUp = sector.performance >= 0;
        const colorClass = isUp ? 'bg-success' : 'bg-danger';
        // Opacity mapping (crude way to do standard deviation heat)
        const heat = Math.min(Math.abs(sector.performance) / 2, 1);
        
        return (
          <div 
            key={sector.id} 
            className={`heatmap-box ${colorClass}`}
            style={{ opacity: 0.4 + (heat * 0.6) }}
          >
            <span className="heatmap-ticker">{sector.ticker}</span>
            <span className="heatmap-perf">{sector.performance}%</span>
            <span className="heatmap-label">{sector.id}</span>
          </div>
        );
      })}
    </div>
  );
}
