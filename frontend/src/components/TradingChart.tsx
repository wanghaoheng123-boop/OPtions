// @ts-nocheck
import { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

interface TradingChartProps {
  data: any[];
  callWall?: number;
  putWall?: number;
}

export default function TradingChart({ data, callWall, putWall }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#cbd5e1',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    try {
        const candlestickSeries = chart.addCandlestickSeries ? chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        }) : chart.addLineSeries({ color: '#10b981' });

        candlestickSeries.setData(data);

        // Overlay Gamma Walls if they exist
        if (callWall && candlestickSeries.createPriceLine) {
            candlestickSeries.createPriceLine({
                price: callWall,
                color: '#10b981',
                lineWidth: 2,
                lineStyle: 2, // Dashed
                axisLabelVisible: true,
                title: 'Call Wall',
            });
        }

        if (putWall && candlestickSeries.createPriceLine) {
            candlestickSeries.createPriceLine({
                price: putWall,
                color: '#ef4444',
                lineWidth: 2,
                lineStyle: 2, // Dashed
                axisLabelVisible: true,
                title: 'Put Wall',
            });
        }
    } catch(err) {
        console.error("TradingView Chart API Error:", err);
    }

    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
           width: chartContainerRef.current.clientWidth,
           height: chartContainerRef.current.clientHeight
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, callWall, putWall]);

  return <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />;
}
