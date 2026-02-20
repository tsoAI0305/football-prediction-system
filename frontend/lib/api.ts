const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getMatches() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/matches`)
    if (!response.ok) throw new Error('Failed to fetch matches')
    return response.json()
  } catch {
    return null
  }
}

export async function getMatchDetails(id: number) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/matches/${id}`)
    if (!response.ok) throw new Error('Failed to fetch match details')
    return response.json()
  } catch {
    return null
  }
}

export async function getPrediction(id: number) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/predictions/${id}`)
    if (!response.ok) throw new Error('Failed to fetch prediction')
    return response.json()
  } catch {
    return null
  }
}

export async function getHistory() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/history`)
    if (!response.ok) throw new Error('Failed to fetch history')
    return response.json()
  } catch {
    return null
  }
}
