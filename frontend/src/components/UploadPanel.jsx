import { useRef, useState } from 'react';
import { uploadTransactions } from '../api';

export default function UploadPanel({ activeSummary, onUploaded, onReset }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [fileName, setFileName] = useState('');
  const [costPct, setCostPct] = useState('30');

  const handleFile = async (file) => {
    if (!file) return;
    setBusy(true);
    setError(null);
    setFileName(file.name);
    try {
      const summary = await uploadTransactions(file, costPct);
      onUploaded(summary);
    } catch (err) {
      setError(err.message);
      setFileName('');
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  return (
    <div className="card upload-card">
      <div className="card-header upload-header">
        <div>
          <h2>Analyze your own data</h2>
          <p className="muted">
            Upload a CSV/Excel of transactions (order id, item, price). If your file
            has no food-cost or margin column, the assumed food-cost % below is used
            to derive margin. Metrics are computed in Python — the AI only explains them.
          </p>
        </div>
        {activeSummary && (
          <span className="meta-pill meta-pill-live">Your dataset</span>
        )}
      </div>

      <div className="upload-actions">
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <label className="cost-field">
          <span className="muted">Assumed food cost</span>
          <span className="cost-input-wrap">
            <input
              type="number"
              min="0"
              max="99"
              step="1"
              value={costPct}
              disabled={busy}
              onChange={(e) => setCostPct(e.target.value)}
            />
            <span className="cost-unit">%</span>
          </span>
        </label>
        <button
          type="button"
          className="btn-primary"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
        >
          {busy ? 'Analyzing…' : 'Upload transactions'}
        </button>
        {activeSummary && (
          <button
            type="button"
            className="btn-ghost"
            disabled={busy}
            onClick={onReset}
          >
            Back to demo data
          </button>
        )}
        {fileName && !error && <span className="upload-filename muted">{fileName}</span>}
      </div>

      {error && <div className="error-banner upload-error">{error}</div>}

      {activeSummary && (
        <div className="upload-summary">
          <span className="upload-stat">
            <strong>{activeSummary.orders.toLocaleString()}</strong> orders
          </span>
          <span className="upload-stat">
            <strong>{activeSummary.line_items.toLocaleString()}</strong> line items
          </span>
          <span className="upload-stat">
            <strong>{activeSummary.distinct_items.toLocaleString()}</strong> menu items
          </span>
        </div>
      )}

      {activeSummary?.warnings?.length > 0 && (
        <ul className="upload-warnings">
          {activeSummary.warnings.map((w) => (
            <li key={w} className="muted">{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
