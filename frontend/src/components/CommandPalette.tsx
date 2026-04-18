// @ts-nocheck
import { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Activity, LayoutDashboard, Search, Trash2 } from 'lucide-react';

interface CommandPaletteProps {
  setViewMode: (m: 'discovery' | 'terminal') => void;
  onRunSearch: () => void;
  onClearTerminalErrors: () => void;
}

export default function CommandPalette({
  setViewMode,
  onRunSearch,
  onClearTerminalErrors,
}: CommandPaletteProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [healthText, setHealthText] = useState<string | null>(null);

  const close = useCallback(() => {
    setOpen(false);
    setQuery('');
    setHealthText(null);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toLowerCase().includes('mac');
      const mod = isMac ? e.metaKey : e.ctrlKey;
      if (mod && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') close();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [close]);

  const runHealth = async () => {
    setHealthText('Checking…');
    try {
      const r = await axios.get('/api/health');
      setHealthText(JSON.stringify(r.data, null, 2));
    } catch (err: any) {
      setHealthText(err?.message || 'Health request failed');
    }
  };

  const actions = useMemo(
    () => [
      {
        id: 'search',
        label: 'Run ticker search',
        hint: 'Uses nav ticker field',
        icon: Search,
        run: () => {
          onRunSearch();
          close();
        },
      },
      {
        id: 'discovery',
        label: 'Open discovery feed',
        icon: LayoutDashboard,
        run: () => {
          setViewMode('discovery');
          close();
        },
      },
      {
        id: 'terminal',
        label: 'Stay on terminal view',
        icon: LayoutDashboard,
        run: () => {
          setViewMode('terminal');
          close();
        },
      },
      {
        id: 'health',
        label: 'GET /api/health',
        icon: Activity,
        run: () => runHealth(),
      },
      {
        id: 'clear-errors',
        label: 'Clear terminal error banners',
        icon: Trash2,
        run: () => {
          onClearTerminalErrors();
          close();
        },
      },
    ],
    [close, onRunSearch, onClearTerminalErrors, setViewMode]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return actions;
    return actions.filter((a) => a.label.toLowerCase().includes(q) || a.hint?.toLowerCase().includes(q));
  }, [actions, query]);

  if (!open) return null;

  return (
    <div
      className="command-palette-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      onClick={close}
    >
      <div className="command-palette" onClick={(e) => e.stopPropagation()}>
        <div className="command-palette__hint">Ctrl/⌘+K to toggle · Esc to close</div>
        <input
          className="command-palette__input"
          autoFocus
          placeholder="Filter commands…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <ul className="command-palette__list">
          {filtered.map((a) => (
            <li key={a.id}>
              <button type="button" className="command-palette__item" onClick={a.run}>
                <a.icon size={16} className="text-accent" />
                <span>{a.label}</span>
              </button>
            </li>
          ))}
        </ul>
        {healthText && (
          <pre className="command-palette__health">{healthText}</pre>
        )}
      </div>
    </div>
  );
}
