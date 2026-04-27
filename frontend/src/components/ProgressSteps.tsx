'use client'

interface Step {
  id: string
  label: string
  icon: string
}

interface ProgressStepsProps {
  steps: Step[]
  currentStep: string
  progress: number
}

/**
 * Match backend step strings (e.g. "Researching topic") to step IDs (e.g. "research").
 * Uses includes() so partial matches work.
 */
function findCurrentIndex(steps: Step[], currentStep: string): number {
  if (!currentStep) return -1
  const lower = currentStep.toLowerCase()

  // Direct ID match first
  const direct = steps.findIndex((s) => s.id === lower)
  if (direct !== -1) return direct

  // Fuzzy match: check if the backend string contains the step ID
  for (let i = 0; i < steps.length; i++) {
    if (lower.includes(steps[i].id)) return i
  }

  // Special mappings for backend strings that don't match IDs
  if (lower.includes('complet') || lower.includes('done') || lower.includes('finished'))
    return steps.length // all done
  if (lower.includes('upload') || lower.includes('saving')) return steps.findIndex((s) => s.id === 'upload')
  if (lower.includes('assembl') || lower.includes('ffmpeg') || lower.includes('stitch'))
    return steps.findIndex((s) => s.id === 'assembly')
  if (lower.includes('tts') || lower.includes('voice') || lower.includes('narrat'))
    return steps.findIndex((s) => s.id === 'audio')
  if (lower.includes('video') || lower.includes('generat'))
    return steps.findIndex((s) => s.id === 'shots')

  return -1
}

export const ProgressSteps = ({
  steps,
  currentStep,
  progress,
}: ProgressStepsProps) => {
  const currentIndex = findCurrentIndex(steps, currentStep)

  return (
    <div className="space-y-4">
      {/* Stepper with connecting lines */}
      <div className="flex items-start justify-between relative">
        {steps.map((step, idx) => {
          const isCompleted = currentIndex > idx || progress >= 100
          const isCurrent = idx === currentIndex && progress < 100
          const isPending = idx > currentIndex && progress < 100

          return (
            <div key={step.id} className="flex flex-col items-center relative z-10" style={{ flex: 1 }}>
              {/* Circle */}
              <div
                className={`w-11 h-11 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-base sm:text-lg font-bold transition-all duration-500 ${
                  isCompleted
                    ? 'bg-green-500 text-white shadow-md shadow-green-500/40'
                    : isCurrent
                      ? 'bg-primary-500/20 border-[3px] border-primary-500 text-primary-400 shadow-lg shadow-primary-500/30 animate-pulse'
                      : 'bg-dark-surface border-2 border-gray-600 text-gray-500'
                }`}
              >
                {isCompleted ? (
                  <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  step.icon
                )}
              </div>

              {/* Label */}
              <p
                className={`text-[10px] sm:text-xs text-center font-medium mt-2 transition-colors duration-300 ${
                  isCompleted
                    ? 'text-green-400'
                    : isCurrent
                      ? 'text-white font-semibold'
                      : 'text-gray-500'
                }`}
              >
                {step.label}
              </p>
            </div>
          )
        })}

        {/* Connecting lines between circles */}
        <div className="absolute top-[22px] sm:top-6 left-0 right-0 flex z-0 px-[8%]">
          {steps.slice(0, -1).map((_, idx) => {
            const segmentDone = currentIndex > idx || progress >= 100
            const segmentActive = idx === currentIndex - 1 || (idx === currentIndex && progress < 100)

            return (
              <div key={idx} className="flex-1 h-[3px] mx-0.5 rounded-full overflow-hidden bg-gray-700 transition-all duration-500">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    segmentDone
                      ? 'w-full bg-green-500'
                      : segmentActive
                        ? 'w-1/2 bg-primary-500'
                        : 'w-0 bg-gray-700'
                  }`}
                />
              </div>
            )
          })}
        </div>
      </div>

      {/* Current Step Details */}
      {currentStep && progress < 100 && (
        <div className="mt-4 p-3 bg-dark-border/50 rounded-lg flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-primary-400 animate-pulse" />
          <div>
            <p className="text-xs text-gray-500">Currently working on</p>
            <p className="text-sm font-semibold text-primary-400">
              {currentStep}
            </p>
          </div>
        </div>
      )}

      {/* All Done */}
      {progress >= 100 && (
        <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg flex items-center gap-3">
          <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-sm font-semibold text-green-400">All steps complete!</p>
        </div>
      )}
    </div>
  )
}
