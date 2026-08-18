const API_BASE = 'http://localhost:8000';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `API error: ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`Fetch error for ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Receipt OCR Scan
  scanReceipt: (imageBase64) =>
    request('/receipts/scan', {
      method: 'POST',
      body: JSON.stringify({ image_base64: imageBase64 })
    }),

  // Receipts CRUD & Summary
  createReceipt: (data) =>
    request('/receipts', {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  getReceipts: (month) =>
    request(month ? `/receipts?month=${month}` : '/receipts'),

  deleteReceipt: (id) =>
    request(`/receipts/${id}`, {
      method: 'DELETE'
    }),

  getSummary: (month) =>
    request(month ? `/receipts/summary?month=${month}` : '/receipts/summary'),

  // Friends CRUD
  getFriends: () => request('/friends'),

  createFriend: (name) =>
    request('/friends', {
      method: 'POST',
      body: JSON.stringify({ name })
    }),

  deleteFriend: (id) =>
    request(`/friends/${id}`, {
      method: 'DELETE'
    }),

  // Splits CRUD & Balances
  createSplits: (splitData) =>
    request('/splits', {
      method: 'POST',
      body: JSON.stringify(splitData)
    }),

  toggleSplitPaid: (id, proofBase64 = null) =>
    request(`/splits/${id}/paid`, {
      method: 'PATCH',
      body: JSON.stringify({ payment_proof_base64: proofBase64 })
    }),

  getBalances: () => request('/splits/balances'),

  getSettledSplits: () => request('/splits/settled'),

  getBudget: () => request('/budgets/current'),

  setBudget: (amount) => request('/budgets', { method: 'POST', body: JSON.stringify({ month: new Date().toISOString().slice(0, 7), amount }) })
};
