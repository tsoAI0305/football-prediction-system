interface ErrorMessageProps {
  message?: string
}

export default function ErrorMessage({ message = '發生錯誤，請稍後再試' }: ErrorMessageProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-5xl mb-4">⚠️</div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">載入失敗</h3>
      <p className="text-text-secondary text-sm">{message}</p>
    </div>
  )
}

export function EmptyState({ message = '目前沒有數據' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-5xl mb-4">📭</div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">無數據</h3>
      <p className="text-text-secondary text-sm">{message}</p>
    </div>
  )
}
