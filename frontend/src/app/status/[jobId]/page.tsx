'use client'

import { useRedirectIfNotAuth, useJobPolling, useAuth } from '@/lib/hooks'
import { useRouter, useParams } from 'next/navigation'
import { useState, useEffect } from 'react'
import { ProgressSteps } from '@/components/ProgressSteps'
import { apiClient } from '@/lib/api'

// Map pipeline steps to estimated remaining time
const getTimeEstimate = (currentStep: string | null): string => {
  if (!currentStep) return ''

  const step = currentStep.toLowerCase()

  if (step.includes('research')) return '~7-8 min remaining'
  if (step.includes('script') || step === 'writing script') return '~6-7 min remaining'
  if (step.includes('review')) return '~5-6 min remaining'
  if (step.includes('shot') || step.includes('shot list')) return '~4-5 min remaining'
  if (step.includes('video') || step.includes('generating video')) return '~2-4 min remaining'
  if (step.includes('audio') || step.includes('tts') || step.includes('generating audio')) return '~1-2 min remaining'
  if (step.includes('assembl') || step.includes('ffmpeg')) return '~30 sec remaining'
  if (step.includes('complete') || step.includes('completed')) return 'Done!'

  return ''
}

const steps = [
  { id: 'research', label: 'Research', icon: '🔍' },
  { id: 'script', label: 'Script', icon: '📝' },
  { id: 'review', label: 'Review', icon: '✓' },
  { id: 'shots', label: 'Shots', icon: '🎬' },
  { id: 'audio', label: 'Audio', icon: '🎙️' },
  { id: 'assembly', label: 'Assembly', icon: '⚙️' },
  { id: 'upload', label: 'Upload', icon: '⬆️' },
]

export default function StatusPage() {
  const { user, loading } = useRedirectIfNotAuth()
  const { session } = useAuth()
  const router = useRouter()
  const params = useParams()
  const jobId = params.jobId as string
  const [cancelling, setCancelling] = useState(false)

  const { status, loading: statusLoading, error } = useJobPolling(jobId)

  const handleCancel = async () => {
    if (!session?.access_token || cancelling) return
    setCancelling(true)
    try {
      await apiClient.cancelJob(session.access_token, jobId)
    } catch (err) {
      console.error('Failed to cancel:', err)
    }
  }

  useEffect(() => {
    if (status?.status === 'completed') {
      setTimeout(() => {
        router.push(`/result/${jobId}`)
      }, 1000)
    }
  }, [status?.status, jobId, router])

  if (loading || statusLoading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin mb-4">
            <div className="text-5xl">⚙️</div>
          </div>
          <p className="text-gray-400 text-lg">Initializing...</p>
        </div>
      </div>
    )
  }

  if (!user || !status) {
    return null
  }

  const isFailed = status.status === 'failed'
  const isComplete = status.status === 'completed'

  return (
    <div className="min-h-screen bg-gradient-dark py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            {isFailed
              ? 'Video Generation Failed'
              : isComplete
                ? 'Video Complete!'
                : 'Generating Your Video'}
          </h1>
          <p className="text-gray-400 text-lg">
            {isFailed
              ? 'Something went wrong. Please try again.'
              : isComplete
                ? 'Your video is ready! Redirecting...'
                : `Step: ${status.current_step || 'Starting...'}`}
          </p>
        </div>

        {/* Progress Section */}
        <div className="card-base mb-8">
          {!isFailed && (
            <>
              {/* Progress Bar */}
              <div className="mb-8">
                <div className="flex justify-between items-center mb-3">
                  <p className="text-sm font-medium">Progress</p>
                  <p className="text-sm font-semibold text-primary-400">
                    {Math.round(status.progress)}%
                  </p>
                </div>
                <div className="w-full h-3 bg-dark-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-primary transition-all duration-300 progress-shimmer rounded-full"
                    style={{ width: `${status.progress}%` }}
                  ></div>
                </div>
                {/* Time Estimate */}
                {getTimeEstimate(status.current_step) && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs text-gray-500">🕐</span>
                    <p className="text-xs text-gray-500">
                      {getTimeEstimate(status.current_step)}
                    </p>
                  </div>
                )}
              </div>

              {/* Step Indicators */}
              <ProgressSteps
                steps={steps}
                currentStep={status.current_step}
                progress={status.progress}
              />
            </>
          )}

          {/* Error Message */}
          {isFailed && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 mb-6">
              <h3 className="font-semibold text-red-400 mb-2">
                Error Details
              </h3>
              <p className="text-red-300 text-sm">
                {status.error_message ||
                  'An unknown error occurred during video generation.'}
              </p>
            </div>
          )}

          {/* Info Box */}
          {!isFailed && (
            <div className="bg-dark-border/50 rounded-lg p-4 mt-8">
              <p className="text-sm text-gray-400">
                💡 Our AI is working on your video. This typically takes 2-4
                minutes. Please keep this page open.
              </p>
              <p className="text-xs text-gray-500 mt-3">
                Times are approximate and vary by topic complexity.
              </p>
            </div>
          )}
        </div>

        {/* Cancel Button — shown while processing */}
        {!isFailed && !isComplete && (
          <div className="flex justify-center mb-6">
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="px-6 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 hover:bg-red-500/20 transition-colors font-semibold"
            >
              {cancelling ? 'Cancelling...' : 'Stop Generation'}
            </button>
          </div>
        )}

        {/* Actions */}
        {isFailed && (
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => router.push('/create')}
              className="button-primary"
            >
              Try Again
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="button-secondary"
            >
              Back to Dashboard
            </button>
          </div>
        )}

        {isComplete && (
          <div className="text-center">
            <p className="text-gray-400">Redirecting to your video...</p>
          </div>
        )}

        {/* Job ID Info */}
        <div className="mt-8 p-4 bg-dark-surface border border-dark-border rounded-lg text-center">
          <p className="text-xs text-gray-500">
            Job ID: <code className="text-gray-400">{jobId}</code>
          </p>
        </div>
      </div>
    </div>
  )
}
