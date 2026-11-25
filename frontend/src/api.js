async function request(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${response.status}`)
  }
  return response.status === 204 ? null : response.json()
}

export const api = {
  campaigns: () => request('/api/campaigns'),
  createCampaign: (data) => request('/api/campaigns', { method: 'POST', body: JSON.stringify(data) }),
  deleteCampaign: (id) => request(`/api/campaigns/${id}`, { method: 'DELETE' }),
  countries: () => request('/api/countries'),
  domains: () => request('/api/references/domains'),
  groups: () => request('/api/references/groups'),
  sources: () => request('/api/references/traffic-sources'),
  offers: () => request('/api/references/offers'),
  campaignOffers: (id) => request(`/api/campaigns/${id}/offers`),
  searchOffers: (id, q) => request(`/api/campaigns/${id}/offers/search?q=${encodeURIComponent(q)}`),
  addOffer: (id, offerId) => request(`/api/campaigns/${id}/offers`, { method: 'POST', body: JSON.stringify({ offer_id: offerId }) }),
  pin: (id, offerId) => request(`/api/campaigns/${id}/offers/${offerId}/pin`, { method: 'POST' }),
  unpin: (id, offerId) => request(`/api/campaigns/${id}/offers/${offerId}/unpin`, { method: 'POST' }),
  deleteOffer: (id, offerId) => request(`/api/campaigns/${id}/offers/${offerId}/delete`, { method: 'POST' }),
  restoreOffer: (id, offerId) => request(`/api/campaigns/${id}/offers/${offerId}/restore`, { method: 'POST' }),
  publish: (id) => request(`/api/campaigns/${id}/offers/publish`, { method: 'POST' }),
  cancel: (id) => request(`/api/campaigns/${id}/offers/cancel`, { method: 'POST' }),
  sync: (id) => request(`/api/campaigns/${id}/offers/sync`, { method: 'POST' }),
}

