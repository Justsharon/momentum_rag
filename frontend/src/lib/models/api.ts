// Provide minimal typing for Vite's import.meta.env to satisfy TypeScript
declare global {
  interface ImportMetaEnv {
    readonly VITE_API_BASE?: string;
  }

  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function handleResponse(res: any) {
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export async function ask(question: string) {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return handleResponse(res);
}

export async function submitFeedback(logId: string, feedback: number) {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ log_id: logId, feedback }),
  });
  return handleResponse(res);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function createCheckIn(payload: any) {
  const res = await fetch(`${API_BASE}/checkins`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function getRecentCheckIns(limit = 30) {
  const res = await fetch(`${API_BASE}/checkins/recent?limit=${limit}`);
  return handleResponse(res);
}

export async function getGoals() {
  const res = await fetch(`${API_BASE}/goals`);
  return handleResponse(res);
}

export async function getProjects() {
  const res = await fetch(`${API_BASE}/projects`);
  return handleResponse(res);
}