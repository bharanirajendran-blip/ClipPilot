'use client'

import { useRedirectIfNotAuth } from '@/lib/hooks'
import { useRouter, useParams } from 'next/navigation'
import { useState, useEffect } from 'react'
import { apiClient, JobResultResponse } from '@/lib/api'
import { useAuth } from '@/lib/hooks'
import { VideoPlayer } from '@/components/VideoPlayer'

export default function ResultPage() {
  const { user, loading } = useRedirectIfNotAuth()
  const { session } = useAuth()
  const router = useRouter()
  const params = useParams()
  const jobId = params.jobId as string

  const [result, setResult] = useState<JobResultResponse | null>(null)
  const [resultLoading, setResultLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [videosRemaining, setVideosRemaining] = useState<number | null>(null)
  const [copied, setCopied] = useState(false)
  const [expandedSection, setExpandedSection] = useState<string | null>(null)

  useEffect(() => {
    const fetchResult = async () => {
      if (!session?.access_token) return

      try {
        const jobResult = await apiClient.getJobResult(
          session.access_token,
          jobId
        )
        setResult(jobResult)

        const profile = await apiClient.getUserProfile(session.access_token)
        setVideosRemaining(profile.videos_remaining)
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load video'
        setError(errorMessage)
      } finally {
        setResultLoading(false)
      }
    }

    fetchResult()
  }, [session?.access_token, jobId])

  const handleDownload = async () => {
    if (!result?.video_url) return
    try {
      const response = await fetch(result.video_url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${result.title || 'clippilot-video'}.mp4`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const handleShare = () => {
    const url = `${window.location.origin}/result/${jobId}`
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const formatData = (data: any): React.ReactNode => {
    if (!data) return null

    if (typeof data === 'string') {
      return <p className="text-gray-300 whitespace-pre-wrap">{data}</p>
    }

    if (typeof data === 'object') {
      if (Array.isArray(data)) {
        return (
          <div className="space-y-3">
            {data.map((item, idx) => (
              <div key={idx} className="p-3 bg-dark-surface/50 rounded border border-dark-border">
                {typeof item === 'object' ? (
                  <pre className="text-xs text-gray-400 overflow-auto max-h-64">
                    {JSON.stringify(item, null, 2)}
                  </pre>
                ) : (
                  <p className="text-gray-300">{String(item)}</p>
                )}
              </div>
            ))}
          </div>
        )
      } else {
        return (
          <pre className="text-xs text-gray-400 bg-dark-surface/50 p-4 rounded border border-dark-border overflow-auto max-h-96">
            {JSON.stringify(data, null, 2)}
          </pre>
        )
      }
    }

    return <p className="text-gray-300">{String(data)}</p>
  }

  const CollapsibleSection = ({
    title,
    id,
    data,
  }: {
    title: string
    id: string
    data: any
  }) => {
    const isExpanded = expandedSection === id

    if (!data) return null

    return (
      <div className="border border-dark-border rounded-lg overflow-hidden">
        <button
          onClick={() => setExpandedSection(isExpanded ? null : id)}
          className="w-full p-4 bg-dark-surface hover:bg-dark-surface/80 transition-colors flex items-center justify-between"
        >
          <h4 className="font-semibold text-gray-200">{title}</h4>
          <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>
        {isExpanded && (
          <div className="p-4 bg-dark-surface/50 border-t border-dark-border">
            {formatData(data)}
          </div>
        )}
      </div>
    )
  }

  if (loading || resultLoading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin mb-4">
            <div className="text-5xl">⚙️</div>
          </div>
          <p className="text-gray-400 text-lg">Loading your video...</p>
        </div>
      </div>
    )
  }

  if (!user || !result) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center py-12 px-4">
        <div className="text-center max-w-md">
          <h2 className="text-2xl font-bold mb-4">Video Not Found</h2>
          <p className="text-gray-400 mb-6">{error || 'Could not load video'}</p>
          <button
            onClick={() => router.push('/create')}
            className="button-primary"
          >
            Create New Video
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-dark py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-primary-400 hover:text-primary-300 font-semibold mb-4 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-bold">Your Video is Ready!</h1>
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8 mb-8">
          {/* Video Player */}
          <div className="lg:col-span-2">
            <VideoPlayer videoUrl={result.video_url} poster={result.thumbnail_url} />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Video Info Card */}
            <div className="card-base">
              <h2 className="text-2xl font-bold mb-4">{result.title}</h2>
              <p className="text-gray-400 mb-6 leading-relaxed">
                {result.description}
              </p>

              {/* Tags */}
              {result.tags && result.tags.length > 0 && (
                <div className="mb-6">
                  <p className="text-sm font-semibold mb-3 text-gray-300">
                    Tags
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {result.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-primary-500/20 border border-primary-500/30 rounded-full text-sm text-primary-300"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  onClick={handleDownload}
                  className="button-primary w-full flex items-center justify-center gap-2"
                >
                  📥 Download Video
                </button>
                <button
                  onClick={handleShare}
                  className="button-secondary w-full flex items-center justify-center gap-2"
                >
                  {copied ? '✓ Copied!' : '🔗 Share Link'}
                </button>
              </div>
            </div>

            {/* Videos Remaining */}
            {videosRemaining !== null && (
              <div className="card-base bg-primary-500/10 border-primary-500/30">
                <p className="text-sm text-gray-400 mb-2">Videos Remaining</p>
                <p className="text-3xl font-bold text-gradient">{videosRemaining}</p>
              </div>
            )}

            {/* Next Steps */}
            <div className="card-base">
              <h3 className="font-semibold mb-4">Next Steps</h3>
              <ul className="space-y-3 text-sm text-gray-400">
                <li className="flex gap-3">
                  <span className="text-lg">📱</span>
                  <span>Share on TikTok, Instagram Reels, or YouTube Shorts</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-lg">✏️</span>
                  <span>Add your own captions or descriptions</span>
                </li>
                <li className="flex gap-3">
                  <span className="text-lg">🎬</span>
                  <span>Create more videos using your remaining quota</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Behind the Scenes Section */}
        {(result.research_data || result.script_data || result.shot_list_data) && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6">Behind the Scenes</h2>
            <div className="space-y-4">
              <CollapsibleSection
                title="🔬 Research Data"
                id="research"
                data={result.research_data}
              />
              <CollapsibleSection
                title="📝 Script"
                id="script"
                data={result.script_data}
              />
              <CollapsibleSection
                title="🎬 Shot List"
                id="shotlist"
                data={result.shot_list_data}
              />
            </div>
          </div>
        )}

        {/* Create Another Section */}
        {videosRemaining !== null && videosRemaining > 0 && (
          <div className="mt-12 p-8 bg-dark-surface border border-dark-border rounded-lg text-center">
            <h3 className="text-2xl font-bold mb-4">Create More Videos</h3>
            <p className="text-gray-400 mb-6">
              You have {videosRemaining} video{videosRemaining !== 1 ? 's' : ''}{' '}
              remaining this month.
            </p>
            <button
              onClick={() => router.push('/create')}
              className="button-primary inline-block"
            >
              Create Another Video
            </button>
          </div>
        )}

        {/* AI Disclaimer */}
        <div className="mt-8 p-4 bg-dark-surface/50 border border-dark-border rounded-lg text-center text-sm text-gray-500">
          <p>
            ⚠️ This video was generated using AI. Please review content for
            accuracy before sharing publicly.
          </p>
        </div>
      </div>
    </div>
  )
}
