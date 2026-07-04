import { useEffect, useState } from 'react';

interface HealthResponse {
  status: string;
  version: string;
  env: string;
}

/**
 * Milestone 2 placeholder shell.
 * Verifies the full stack (Vite → proxy → FastAPI) is wired correctly.
 * The real chat UI (sidebar, history, settings) lands in Milestone 7.
 */
export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json() as Promise<HealthResponse>)
      .then(setHealth)
      .catch(() => setError('Backend not reachable'));
  }, []);

  return (
    <div className="flex h-screen items-center justify-center bg-surface-dark text-gray-100">
      <div className="rounded-xl bg-panel-dark p-8 text-center shadow-lg">
        <h1 className="mb-2 text-3xl font-bold text-accent">EXO</h1>
        <p className="text-sm text-gray-400">AI Desktop Assistant — skeleton build</p>
        <p className="mt-4 text-xs">
          {health && (
            <span className="text-green-400">
              Backend online · v{health.version} · {health.env}
            </span>
          )}
          {error && <span className="text-red-400">{error}</span>}
          {!health && !error && <span className="text-gray-500">Checking backend…</span>}
        </p>
      </div>
    </div>
  );
}
