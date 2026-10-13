const API_BASE_URL = 'http://127.0.0.1:8000'

export async function getStationStatus() {
  const response = await fetch(`${API_BASE_URL}/stations/status`)

  if (!response.ok) {
    throw new Error(`Failed to load stations (HTTP ${response.status})`)
  }

  return response.json()
}
