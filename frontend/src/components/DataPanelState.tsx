// @ts-nocheck
import React from 'react';

type Props = {
  mode: 'loading' | 'error' | 'empty' | 'stale';
  title?: string;
  message: string;
  onRetry?: () => void;
};

export default function DataPanelState({ mode, title, message, onRetry }: Props) {
  const color = mode === 'error' ? '#ff453a' : mode === 'stale' ? '#f59e0b' : '#a0a0ab';
  return (
    <div className="terminal-loading" style={{ color }}>
      {title ? <div style={{ fontWeight: 700, marginBottom: 6 }}>{title}</div> : null}
      <div>{message}</div>
      {onRetry ? (
        <button
          type="button"
          className="terminal-btn-primary"
          style={{ marginTop: 10 }}
          onClick={onRetry}
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

