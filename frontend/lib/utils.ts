export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.7) return 'text-primary'
  if (confidence >= 0.5) return 'text-accent'
  return 'text-red-500'
}

export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.7) return '高信心'
  if (confidence >= 0.5) return '中等信心'
  return '低信心'
}

export function getFormColor(result: string): string {
  switch (result) {
    case 'W': return 'bg-primary'
    case 'D': return 'bg-accent'
    case 'L': return 'bg-red-500'
    default: return 'bg-gray-500'
  }
}
