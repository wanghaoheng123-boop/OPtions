import { useEffect, useState } from 'react';
import axios from 'axios';

interface SectorData {
  id: string;
  ticker: string;
  performance: number;
}

export default function SectorHeatmap() {
  const [sectors, setSectors] = useState<SectorData[]>([]);

  useEffect(() => {
    axios.get('/api/heatmap').then(res => setSectors(res.data));
  }, []);

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
