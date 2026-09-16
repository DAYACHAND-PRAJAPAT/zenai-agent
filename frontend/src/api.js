const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function sendChatMessage(message) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error(`Chat request failed: ${res.status}`);
  return res.json();
}

export async function fetchDashboardRequests(limit = 50) {
  const res = await fetch(`${API_BASE}/dashboard/requests?limit=${limit}`);
  if (!res.ok) throw new Error(`Dashboard fetch failed: ${res.status}`);
  return res.json();
}

export async function runRegulatoryRadar() {
  const res = await fetch(`${API_BASE}/regulatory-radar/run`);
  if (!res.ok) throw new Error(`Regulatory radar failed: ${res.status}`);
  return res.json();
}

export async function analyzeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/analyze-document`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Document analysis failed: ${res.status}`);
  return res.json();
}
