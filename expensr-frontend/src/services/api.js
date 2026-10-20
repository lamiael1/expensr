const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`Error HTTP ${response.status}`);
  }

  return response.json();
}

export function getMonitorOverview() {
  return request("/monitor/overview");
}

export function getExpenses() {
  return request("/expenses/");
}

export async function extractInvoice(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/extract-invoice`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Error HTTP ${response.status}`);
  }

  return response.json();
}

export async function createExpense(expense) {
  const response = await fetch(`${API_BASE_URL}/expenses/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(expense),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Error HTTP ${response.status}`);
  }

  return response.json();
}

export async function sendChatMessage(message, empleado) {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, empleado }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Error HTTP ${response.status}`);
  }

  return response.json();
}
