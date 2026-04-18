// @ts-nocheck
import { useEffect, useState } from 'react';
import axios from 'axios';

export default function MethodologyDrawer({ panelId }: { panelId: string }) {
  const [open, setOpen] = useState(false);
  const [doc, setDoc] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setErr(null);
    axios
      .get(`/api/methodology/${encodeURIComponent(panelId)}`)
      .then((res) => setDoc(res.data))
      .catch((e) => {
        const d = e?.response?.data?.detail;
        setErr(typeof d === 'string' ? d : e?.message || 'Failed to load methodology');
      });
  }, [open, panelId]);

  return (
    <div className="methodology-drawer">
      <button
        type="button"
        className="methodology-drawer__toggle"
        onClick={(ev) => {
          ev.stopPropagation();
          setOpen((v) => !v);
        }}
      >
        {open ? 'Hide' : 'Method'}
      </button>
      {open && (
        <div className="methodology-drawer__body">
          {err && <p className="text-danger text-xs">{err}</p>}
          {doc && (
            <>
              <p className="methodology-drawer__title">{doc.title}</p>
              <div className="methodology-drawer__section">
                <span className="methodology-drawer__label">Inputs</span>
                <ul>
                  {(doc.inputs || []).map((x: string, i: number) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
              <div className="methodology-drawer__section">
                <span className="methodology-drawer__label">Method</span>
                <ul>
                  {(doc.method || []).map((x: string, i: number) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
              <div className="methodology-drawer__section">
                <span className="methodology-drawer__label">Limits</span>
                <ul>
                  {(doc.limits || []).map((x: string, i: number) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
              <div className="methodology-drawer__section">
                <span className="methodology-drawer__label">Code paths</span>
                <ul className="methodology-drawer__code">
                  {(doc.code_paths || []).map((x: string, i: number) => (
                    <li key={i}>
                      <code>{x}</code>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
