// @ts-nocheck
import React, { useState, useEffect } from 'react';
import DataPanelState from './DataPanelState';

export default function StatArbHeatmap() {
    const [pairs, setPairs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);

    const load = () => {
        setLoading(true);
        const parseSafe = async (res: Response) => {
            const text = await res.text();
            if (!text) return null;
            try {
                return JSON.parse(text);
            } catch {
                return { detail: text.slice(0, 240) };
            }
        };

        fetch('/api/statarb')
            .then(async (res) => {
                const data = await parseSafe(res);
                if (!res.ok) {
                    throw new Error(data?.detail || 'StatArb request failed');
                }
                return data;
            })
            .then(data => {
                if (Array.isArray(data?.pairs)) {
                    setPairs(data.pairs);
                    setError(null);
                    setLastUpdated(new Date().toISOString());
                } else {
                    setPairs([]);
                    setError('StatArb response shape is invalid.');
                }
                setLoading(false);
            })
            .catch(e => {
                console.error("Failed to load pairs", e);
                setError(e?.message || 'Failed to load pairs');
                setLoading(false);
            });
    };

    useEffect(() => {
        load();
    }, []);

    const getColor = (zScore) => {
        if (zScore > 2.0) return '#ff3b30'; // Red - Overvalued
        if (zScore < -2.0) return '#34c759'; // Green - Undervalued
        return '#3a3a3c'; // Muted Gray - Normal
    };

    return (
        <div className="terminal-panel flex-col" style={{ padding: '16px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#a0a0ab', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Statistical Arbitrage Matrix <span style={{color: '#ff9f0a'}}>90D Z-SCORES</span>
            </h3>
            
            {loading ? (
                <DataPanelState mode="loading" message="Scanning historic correlations..." />
            ) : error ? (
                <DataPanelState mode="error" title="StatArb unavailable" message={error} onRetry={load} />
            ) : !pairs.length ? (
                <DataPanelState mode="empty" title="No StatArb pairs" message="No valid pairs were returned for this run." onRetry={load} />
            ) : (
                <div>
                    <div className="text-xs text-secondary mb-2">Last updated: {lastUpdated ? lastUpdated.replace('T', ' ').slice(0, 19) : 'n/a'}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '8px' }}>
                    {pairs.map((p, i) => (
                        <div key={i} style={{
                            backgroundColor: getColor(p.z_score),
                            borderRadius: '6px',
                            padding: '12px',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid rgba(255,255,255,0.1)',
                            boxShadow: p.z_score > 2.0 || p.z_score < -2.0 ? `0 0 10px ${getColor(p.z_score)}` : 'none',
                            transition: 'all 0.3s ease'
                        }}>
                            <span style={{ fontWeight: 'bold', fontSize: '15px' }}>{p.pair}</span>
                            <span style={{ fontSize: '18px', margin: '4px 0', fontWeight: '800' }}>
                                {p.z_score > 0 ? '+' : ''}{p.z_score.toFixed(2)}
                            </span>
                            <span style={{ fontSize: '10px', opacity: 0.8 }}>SPREAD: {p.current_spread.toFixed(2)}</span>
                            { (p.z_score > 2.0 || p.z_score < -2.0) && (
                                <div style={{ fontSize: '10px', marginTop: '6px', fontWeight: 'bold', backgroundColor: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '4px' }}>
                                    {p.action}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
                </div>
            )}
        </div>
    );
}
