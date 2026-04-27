// @ts-nocheck
import { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  CandlestickSeries,
} from 'lightweight-charts';

interface TradingChartProps {
  data: any[];
  callWall?: number;
  putWall?: number;
  onChartError?: (msg: string) => void;
}

/**
 * lightweight-charts v5: use chart.addSeries(CandlestickSeries, options).
 * Data: { time: 'YYYY-MM-DD', open, high, low, close }[]
 */
export default function TradingChart({ data, callWall, putWall, onChartError }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const onChartErrorRef = useRef(onChartError);
  onChartErrorRef.current = onChartError;

  useEffect(() => {
    if (!chartContainerRef.current) return;
    if (!data || !Array.isArray(data) || data.length === 0) {
      return;
    }

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
      const candleOptions = {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      };

      const candlestickSeries =
        typeof chart.addSeries === 'function'
          ? chart.addSeries(CandlestickSeries, candleOptions)
          : chart.addCandlestickSeries?.(candleOptions) ||
            chart.addLineSeries({ color: '#10b981' });

      const normalized = data.map((bar: any) => ({
        time: bar.time,
        open: Number(bar.open),
        high: Number(bar.high),
        low: Number(bar.low),
        close: Number(bar.close),
      }));

      candlestickSeries.setData(normalized);

      if (callWall && candlestickSeries.createPriceLine) {
        candlestickSeries.createPriceLine({
          price: callWall,
          color: '#10b981',
          lineWidth: 2,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'Call Wall',
        });
      }

      if (putWall && candlestickSeries.createPriceLine) {
        candlestickSeries.createPriceLine({
          price: putWall,
          color: '#ef4444',
          lineWidth: 2,
          lineStyle: 2,
          axisLabelVisible: true,
          title: 'Put Wall',
        });
      }
    } catch (err: any) {
      console.error('TradingChart error:', err);
      onChartErrorRef.current?.(err?.message || String(err));
    }

    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
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
