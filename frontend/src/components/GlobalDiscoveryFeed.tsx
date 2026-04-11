// @ts-nocheck
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Target, AlertTriangle, Zap, TrendingUp, TrendingDown } from 'lucide-react';

interface GlobalDiscoveryFeedProps {
  onSelectTicker: (ticker: string) => void;
}

export default function GlobalDiscoveryFeed({ onSelectTicker }: GlobalDiscoveryFeedProps) {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Poll the backend screener
    axios.get('/api/screener')
      .then(res => {
        if (res.data.top_opportunities) {
          setOpportunities(res.data.top_opportunities);
        }
        setLoading(false);
      })
      .catch(e => {
        console.error("Screener failed:", e);
        setLoading(false);
      });
  }, []);

  return (
    <div className="terminal-panel" style={{ minHeight: '80vh', padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px' }}>
         <Zap size={24} color="#ff9f0a" style={{ marginRight: '10px' }} />
         <div>
            <h2 style={{ fontSize: '24px', margin: 0, fontWeight: 800 }}>Institutional Discovery Feed</h2>
            <p style={{ color: '#a0a0ab', fontSize: '13px', margin: '4px 0 0 0' }}>AI autonomously screening Equities, Commodities, and Bonds for mathematically actionable edges.</p>
         </div>
      </div>

      {loading ? (
        <div className="terminal-loading" style={{ height: '300px' }}>
           <div className="pulsing-text">Scanning Global Liquidity Universe... This takes processing power.</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {opportunities.map((opp, idx) => {
            const isDanger = opp.urgency === 'CRITICAL';
            
            return (
              <div 
                key={idx} 
                onClick={() => onSelectTicker(opp.ticker)}
                style={{
                  backgroundColor: '#1c1c1e',
                  border: `1px solid ${isDanger ? '#ff3b30' : 'rgba(255,255,255,0.1)'}`,
                  borderRadius: '8px',
                  padding: '20px',
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  position: 'relative',
                  overflow: 'hidden'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-4px)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                 {isDanger && (
                    <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '4px', backgroundColor: '#ff3b30' }} />
                 )}
                 
                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                       <h3 style={{ fontSize: '32px', margin: 0, fontWeight: 900 }}>{opp.ticker}</h3>
                       <span style={{ fontSize: '12px', color: '#ff9f0a', fontWeight: 'bold' }}>{opp.category.toUpperCase()}</span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                       <div style={{ fontSize: '14px', color: '#a0a0ab' }}>Spot</div>
                       <div style={{ fontSize: '20px', fontWeight: 'bold' }}>${opp.current_price}</div>
                    </div>
                 </div>

                 <div style={{ marginTop: '20px', padding: '12px', backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                       {opp.z_score > 0 ? <TrendingUp size={16} color="#ff3b30" /> : <TrendingDown size={16} color="#34c759" />}
                       <span style={{ marginLeft: '8px', fontWeight: 'bold', fontSize: '13px' }}>
                          Z-SCORE: {opp.z_score > 0 ? '+' : ''}{opp.z_score}
                       </span>
                    </div>
                    <p style={{ margin: '0 0 12px 0', fontSize: '13px', lineHeight: '1.5', color: '#d1d1d6' }}>
                       {opp.thesis}
                    </p>
                    <div style={{ 
                       display: 'inline-block', 
                       backgroundColor: isDanger ? 'rgba(255,59,48,0.2)' : 'rgba(52,199,89,0.2)',
                       color: isDanger ? '#ff3b30' : '#34c759',
                       padding: '4px 10px',
                       borderRadius: '4px',
                       fontSize: '11px',
                       fontWeight: 900,
                       letterSpacing: '1px'
                    }}>
                       ACTION: {opp.action}
                    </div>
                 </div>
                 
                 <div style={{ marginTop: '16px', fontSize: '12px', color: '#a0a0ab', display: 'flex', alignItems: 'center' }}>
                    <Target size={14} style={{ marginRight: '6px' }} />
                    Click to drill down into Option Chain analytics
                 </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
