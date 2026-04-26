/**
 * Reusable skeleton loading components using Tailwind CSS animations
 * Perfect for creating loading placeholders that match your content layout
 */

/**
 * SkeletonLine - A thin horizontal line for text content
 * Use for titles, labels, and short text
 */
export function SkeletonLine({ className = '' }: { className?: string }) {
  return (
    <div
      className={`h-4 bg-gray-700/50 rounded animate-pulse ${className}`}
    />
  )
}

/**
 * SkeletonBlock - A rectangular block for larger content areas
 * Use for images, video players, and major sections
 */
export function SkeletonBlock({ className = '' }: { className?: string }) {
  return (
    <div
      className={`bg-gray-700/50 rounded animate-pulse ${className}`}
    />
  )
}

/**
 * SkeletonCard - A card-shaped skeleton with padding and border
 * Use as a wrapper for loading card content
 */
export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div
      className={`p-4 bg-gray-700/50 rounded-lg border border-gray-700/30 animate-pulse ${className}`}
    />
  )
}

/**
 * SkeletonVideoResult - Skeleton for the result page layout
 * Shows placeholder for video player, title, description, and metadata
 */
export function SkeletonVideoResult() {
  return (
    <div className="min-h-screen bg-gradient-dark py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <SkeletonLine className="w-32 mb-4" />
          <SkeletonLine className="w-64 h-10" />
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8 mb-8">
          {/* Video Player */}
          <div className="lg:col-span-2">
            <SkeletonBlock className="w-full aspect-video rounded-lg" />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Video Info Card */}
            <div className="card-base">
              <SkeletonLine className="w-3/4 h-8 mb-4" />
              <div className="space-y-3 mb-6">
                <SkeletonLine />
                <SkeletonLine className="w-5/6" />
                <SkeletonLine className="w-4/6" />
              </div>

              {/* Tags */}
              <div className="mb-6">
                <SkeletonLine className="w-16 mb-3" />
                <div className="flex flex-wrap gap-2">
                  {[1, 2, 3].map((i) => (
                    <SkeletonBlock key={i} className="w-20 h-8" />
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <SkeletonBlock className="w-full h-10 rounded-lg" />
                <SkeletonBlock className="w-full h-10 rounded-lg" />
              </div>
            </div>

            {/* Videos Remaining */}
            <div className="card-base bg-primary-500/10 border-primary-500/30">
              <SkeletonLine className="w-32 mb-2" />
              <SkeletonLine className="w-20 h-10" />
            </div>

            {/* Next Steps */}
            <div className="card-base">
              <SkeletonLine className="w-24 mb-4" />
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <SkeletonLine key={i} className="w-5/6" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * SkeletonDashboardCard - Skeleton for a single job card in the dashboard
 * Shows placeholder for thumbnail, title, description, and metadata
 */
export function SkeletonDashboardCard() {
  return (
    <div className="card-base">
      {/* Thumbnail */}
      <SkeletonBlock className="w-full h-40 mb-4 rounded-lg" />

      {/* Title */}
      <SkeletonLine className="w-3/4 h-5 mb-2" />

      {/* Description */}
      <div className="space-y-2 mb-3">
        <SkeletonLine />
        <SkeletonLine className="w-5/6" />
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2 mb-3">
        {[1, 2].map((i) => (
          <SkeletonBlock key={i} className="w-16 h-6 rounded" />
        ))}
      </div>

      {/* Date + Delete */}
      <div className="flex items-center justify-between">
        <SkeletonLine className="w-20" />
        <SkeletonLine className="w-16" />
      </div>
    </div>
  )
}

/**
 * SkeletonDashboard - Full skeleton for the dashboard page
 * Shows placeholder for stats and a grid of job cards
 */
export function SkeletonDashboard() {
  return (
    <div className="min-h-screen bg-gradient-dark py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <SkeletonLine className="w-96 h-10 mb-2" />
          <SkeletonLine className="w-72" />
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card-base">
              <SkeletonLine className="w-32 mb-2" />
              <SkeletonLine className="w-20 h-10 mb-3" />
              <SkeletonLine className="w-48" />
            </div>
          ))}
        </div>

        {/* Create Button */}
        <div className="mb-12">
          <SkeletonBlock className="h-12 w-48 rounded-lg" />
        </div>

        {/* Job Cards Grid */}
        <div>
          <SkeletonLine className="w-40 h-8 mb-6" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <SkeletonDashboardCard key={i} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
