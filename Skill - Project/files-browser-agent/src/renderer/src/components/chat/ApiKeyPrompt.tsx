import { useState } from 'react';

export function ApiKeyPrompt({ onSaved }: { onSaved: () => void }) {
  const [key, setKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    if (!key.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await window.api.setKey(key.trim());
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setSaving(false);
    }
  };

  const clearStored = async () => {
    setClearing(true);
    setError(null);
    try {
      await window.api.clearStoredKey();
      setKey('');
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="apikey">
      <h3>Connect Gemini</h3>
      <p className="muted">
        Enter your Google AI Studio API key. It is kept only for this app session and will be
        requested again after restart.
      </p>
      <input
        className="composer"
        type="password"
        placeholder="AIza..."
        value={key}
        onChange={(e) => setKey(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && save()}
      />
      {error && <div className="apikey__error">⚠ {error}</div>}
      <button className="btn" onClick={save} disabled={saving || !key.trim()}>
        {saving ? 'Saving…' : 'Save key'}
      </button>
      <button className="btn" onClick={clearStored} disabled={clearing || saving}>
        {clearing ? 'Clearing…' : 'Reset stored key'}
      </button>
    </div>
  );
}
