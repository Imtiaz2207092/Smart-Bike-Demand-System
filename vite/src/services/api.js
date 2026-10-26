const API_BASE_URL = 'http://127.0.0.1:8000'

async function getJson(path, resourceName) {
  const response = await fetch(`${API_BASE_URL}${path}`)

  if (!response.ok) {
    throw new Error(`Failed to load ${resourceName} (HTTP ${response.status})`)
  }

  return response.json()
}

export async function getStationStatus() {
  const response = await getJson('/stations/status', 'stations')
  if (Array.isArray(response)) return response
  if (response && Array.isArray(response.stations)) return response.stations
  throw new Error('The station API returned an unexpected response.')
}

export async function getLiveStations() {
  const response = await getJson('/stations/live', 'live stations')
  if (response && Array.isArray(response.stations)) return response
  if (Array.isArray(response)) return { stations: response, fetch_status: 'ok', stale: false }
  throw new Error('The live station API returned an unexpected response.')
}

export async function getModelComparison() {
  return getJson('/models/comparison', 'model comparison')
}
