import { useEffect, useState } from 'react';
import axios from 'axios';

export default function MacroPanel() {
  const [macro, setMacro] = useState<any>(null);

  useEffect(() => {
    axios.get('/api/macro').then(res => setMacro(res.data));
  }, []);

  if (!macro) return <div className="terminal-loading">Loading FED Data...</div>;

  return (
    <div className="macro-container">
      <div className="macro-row">
        <span>10Y Treasury (DGS10)</span>
        <span className="text-accent">{macro.DGS10}%</span>
      </div>
      <div className="macro-row">
        <span>SOFR</span>
        <span className="text-secondary">{macro.SOFR}%</span>
      </div>
      <div className="macro-row">
        <span>CPI YoY</span>
        <span className="text-red">{macro.CPIAUCSL_YoY}%</span>
      </div>
      <div className="macro-row mt-tight border-top">
        <span className="text-secondary text-sm">Source: federalreserve.gov via polymarket-style feed</span>
      </div>
    </div>
  );
}
