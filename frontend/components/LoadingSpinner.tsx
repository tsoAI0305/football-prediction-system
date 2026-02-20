export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="w-10 h-10 border-4 border-gray-700 border-t-primary rounded-full animate-spin" />
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-surface border border-gray-800 rounded-xl p-5 animate-pulse">
      <div className="flex justify-between mb-3">
        <div className="h-4 bg-gray-700 rounded w-24" />
        <div className="h-4 bg-gray-700 rounded w-32" />
      </div>
      <div className="flex items-center justify-between my-4">
        <div className="h-5 bg-gray-700 rounded w-28" />
        <div className="h-6 bg-gray-700 rounded w-8" />
        <div className="h-5 bg-gray-700 rounded w-28" />
      </div>
      <div className="border-t border-gray-800 pt-3 mt-3">
        <div className="h-3 bg-gray-700 rounded w-full" />
      </div>
    </div>
  )
}
