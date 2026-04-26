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

export const ProgressSteps = ({
  steps,
  currentStep,
  progress,
}: ProgressStepsProps) => {
  const currentIndex = steps.findIndex((s) => s.id === currentStep)

  return (
    <div className="space-y-6">
      {/* Steps Grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-7 gap-2 sm:gap-3">
        {steps.map((step, idx) => {
          const isCompleted = idx < currentIndex
          const isCurrent = idx === currentIndex
          const isPending = idx > currentIndex

          return (
            <div key={step.id} className="flex flex-col items-center">
              {/* Step Circle */}
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center font-semibold text-lg mb-2 transition-all ${
                  isCompleted
                    ? 'bg-green-500/20 border-2 border-green-500 text-green-400'
                    : isCurrent
                      ? 'bg-primary-500/20 border-2 border-primary-500 text-primary-400 scale-110 shadow-lg shadow-primary-500/30'
                      : 'bg-dark-border border-2 border-dark-border text-gray-500'
                }`}
              >
                {isCompleted ? '✓' : step.icon}
              </div>

              {/* Step Label */}
              <p
                className={`text-xs text-center font-medium hidden sm:block ${
                  isCompleted || isCurrent ? 'text-white' : 'text-gray-500'
                }`}
              >
                {step.label}
              </p>
            </div>
          )
        })}
      </div>

      {/* Connected Line */}
      <div className="hidden md:block relative h-2 bg-dark-border rounded-full overflow-hidden mt-6">
        <div
          className="h-full bg-gradient-primary transition-all duration-300 rounded-full"
          style={{ width: `${(currentIndex / (steps.length - 1)) * 100}%` }}
        />
      </div>

      {/* Current Step Details */}
      {currentStep && (
        <div className="mt-6 p-4 bg-dark-border/50 rounded-lg">
          <p className="text-sm text-gray-400 mb-1">Current Step</p>
          <p className="text-lg font-semibold text-primary-400">
            {steps.find((s) => s.id === currentStep)?.label || 'Processing'}
          </p>
        </div>
      )}
    </div>
  )
}
