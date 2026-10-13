const API_BASE_URL = 'http://127.0.0.1:8000'

async function getJson(path, resourceName) {
  const response = await fetch(`${API_BASE_URL}${path}`)

  if (!response.ok) {
    throw new Error(`Failed to load ${resourceName} (HTTP ${response.status})`)
  }

  return response.json()
}

export async function getStationStatus() {
  return getJson('/stations/status', 'stations')
}

export async function getModelComparison() {
  return getJson('/models/comparison', 'model comparison')
}
