const API_BASE = import.meta.env.VITE_API_BASE ?? '';
const API_KEY = import.meta.env.VITE_API_KEY ?? '';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || response.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return response.json();
}

function withSession(path, sessionId) {
  if (!sessionId) return path;
  const sep = path.includes('?') ? '&' : '?';
  return `${path}${sep}session_id=${encodeURIComponent(sessionId)}`;
}

export function fetchMenuMatrix(sessionId) {
  return request(withSession('/menu-matrix', sessionId));
}

export function fetchMenuAnalysis(sessionId) {
  return request(withSession('/menu-analysis', sessionId));
}

export function fetchAssociations(limit = 10, sessionId) {
  return request(withSession(`/associations?limit=${limit}`, sessionId));
}

export function sendChat(question, sessionId) {
  return request('/chat', {
    method: 'POST',
    body: JSON.stringify({ question, session_id: sessionId }),
  });
}

export async function uploadTransactions(file, costPct) {
  const form = new FormData();
  form.append('file', file);
  if (costPct !== undefined && costPct !== null && costPct !== '') {
    form.append('cost_pct', costPct);
  }

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    headers: {
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
    },
    body: form,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail || response.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return response.json();
}
