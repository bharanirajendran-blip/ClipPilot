'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { apiClient, JobResultResponse } from '@/lib/api'
import { VideoPlayer } from '@/components/VideoPlayer'

export default function SharePage() {
  const params = useParams()
  const jobId = params.jobId as string
  const [result, setResult] = useState<JobResultResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!jobId) return

    const fetchResult = async () => {
      try {
        const data = await apiClient.getSharedResult(jobId)
        setResult(data)
      } catch (err) {
        setError('This video is not available or has been removed.')
      } finally {
        setLoading(false)
      }
    }

    fetchResult()
  }, [jobId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin mb-4">
            <div className="text-5xl">🎬</div>
          </div>
          <p className="text-gray-400 text-lg">Loading video...</p>
        </div>
      </div>
    )
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-5xl mb-4">😔</div>
          <h1 className="text-2xl font-bold mb-2">Video Not Found</h1>
          <p className="text-gray-400 mb-6">{error || 'This video is not available.'}</p>
          <a
            href="/"
            className="button-primary inline-block"
          >
            Go to ClipPilot
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-dark py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-2">{result.title}</h1>
          <p className="text-gray-400">{result.description}</p>
        </div>

        {/* Video Player */}
        <div className="mb-8">
          <VideoPlayer
            videoUrl={result.video_url}
            poster={result.thumbnail_url}
          />
        </div>

        {/* Tags */}
        {result.tags && result.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 justify-center mb-8">
            {result.tags.map((tag, i) => (
              <span
                key={i}
                className="px-3 py-1 bg-dark-border rounded-full text-sm text-gray-300"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}

        {/* CTA */}
        <div className="text-center mt-12 p-6 bg-dark-surface border border-dark-border rounded-lg">
          <p className="text-gray-400 mb-4">
            Made with ClipPilot — AI-powered short video generator
          </p>
          <a
            href="/"
            className="button-primary inline-block"
          >
            Create Your Own Video
          </a>
        </div>
      </div>
    </div>
  )
}
