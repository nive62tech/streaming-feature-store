const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI(path: string, options?: RequestInit) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => fetchAPI("/health"),
  stats: () => fetchAPI("/stats"),
  getFeature: (entityId: string) =>
    fetchAPI(`/features/${entityId}?include_embeddings=false`),
  schema: (limit = 27) =>
    fetchAPI(`/schema?limit=${limit}&exclude_embeddings=true`),
  driftLatest: () => fetchAPI("/drift/latest"),
  driftHistory: (limit = 30) => fetchAPI(`/drift/history?limit=${limit}`),
  triggerDriftCheck: () =>
    fetchAPI("/drift/check?window_minutes=60", { method: "POST" }),
  snapshotInfo: () => fetchAPI("/drift/snapshot"),
  activeModel: () => fetchAPI("/model/active"),
  modelVersions: () => fetchAPI("/model/versions"),
  retrainingHistory: () => fetchAPI("/retraining/history"),
  retrainingStatus: () => fetchAPI("/retraining/status"),
  triggerRetraining: (force = true) =>
    fetchAPI(`/retraining/trigger?force=${force}`, { method: "POST" }),
};