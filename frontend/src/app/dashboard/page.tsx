'use client'

import { useRedirectIfNotAuth } from '@/lib/hooks'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/hooks'
import { apiClient, Job } from '@/lib/api'
import { SkeletonDashboard } from '@/components/Skeleton'

export default function DashboardPage() {
  const { user, loading } = useRedirectIfNotAuth()
  const { session } = useAuth()
  const router = useRouter()

  const [jobs, setJobs] = useState<Job[]>([])
  const [videosRemaining, setVideosRemaining] = useState<number | null>(null)
  const [jobsLoading, setJobsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!session?.access_token) return

      try {
        const [userJobs, profile] = await Promise.all([
          apiClient.getUserJobs(session.access_token),
          apiClient.getUserProfile(session.access_token),
        ])

        setJobs(userJobs)
        setVideosRemaining(profile.videos_remaining)
        setError(null)
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load dashboard'
        setError(errorMessage)
      } finally {
        setJobsLoading(false)
      }
    }

    fetchData()
  }, [session?.access_token])

  if (loading || jobsLoading) {
    return <SkeletonDashboard />
  }

  if (!user) {
    return null
  }

  const completedJobs = jobs.filter((j) => j.status === 'completed')
  const processingJobs = jobs.filter((j) => j.status === 'processing' || j.status === 'queued')

  const handleDelete = async (e: React.MouseEvent, jobId: string) => {
    e.stopPropagation()
    if (!session?.access_token) return
    if (!confirm('Are you sure you want to delete this video?')) return

    try {
      await apiClient.deleteJob(session.access_token, jobId)
      setJobs(jobs.filter((j) => j.id !== jobId))
    } catch (err) {
      console.error('Failed to delete:', err)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <div className="min-h-screen bg-gradient-dark py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-2">
            Welcome back, {user.email?.split('@')[0]}!
          </h1>
          <p className="text-gray-400 text-lg">
            Manage and view all your generated videos.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Videos Remaining */}
          <div className="card-base bg-primary-500/10 border-primary-500/30">
            <p className="text-sm text-gray-400 mb-2">Videos Remaining</p>
            <p className="text-4xl font-bold text-gradient">
              {videosRemaining === null ? '-' : videosRemaining}
            </p>
            <p className="text-xs text-gray-500 mt-3">
              Free videos available this month
            </p>
          </div>

          {/* Videos Created */}
          <div className="card-base bg-secondary-500/10 border-secondary-500/30">
            <p className="text-sm text-gray-400 mb-2">Videos Created</p>
            <p className="text-4xl font-bold text-gradient">
              {completedJobs.length}
            </p>
            <p className="text-xs text-gray-500 mt-3">
              Completed videos
            </p>
          </div>

          {/* Processing */}
          <div className="card-base bg-blue-500/10 border-blue-500/30">
            <p className="text-sm text-gray-400 mb-2">In Progress</p>
            <p className="text-4xl font-bold text-blue-400">
              {processingJobs.length}
            </p>
            <p className="text-xs text-gray-500 mt-3">
              Videos being generated
            </p>
          </div>
        </div>

        {/* Create Button */}
        {videosRemaining !== null && videosRemaining > 0 && (
          <div className="mb-12">
            <button
              onClick={() => router.push('/create')}
              className="button-primary text-lg py-4 px-8"
            >
              Create New Video
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Processing Videos */}
        {processingJobs.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold mb-6">In Progress</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {processingJobs.map((job) => (
                <div
                  key={job.id}
                  className="card-base cursor-pointer"
                  onClick={() => router.push(`/status/${job.id}`)}
                >
                  <div className="h-40 bg-dark-border/50 rounded-lg mb-4 flex items-center justify-center">
                    <div className="text-center">
                      <div className="inline-block animate-spin mb-2">
                        <div className="text-3xl">⚙️</div>
                      </div>
                      <p className="text-sm text-gray-400">
                        {job.progress}% complete
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mb-2 truncate">
                    {job.topic}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatDate(job.created_at)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Completed Videos */}
        {completedJobs.length > 0 ? (
          <div>
            <h2 className="text-2xl font-bold mb-6">Your Videos</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {completedJobs.map((job) => (
                <div
                  key={job.id}
                  className="card-base cursor-pointer group"
                  onClick={() => router.push(`/result/${job.id}`)}
                >
                  {/* Thumbnail */}
                  <div className="relative h-40 bg-dark-border/50 rounded-lg mb-4 overflow-hidden group-hover:opacity-80 transition-opacity">
                    {job.thumbnail_url && (
                      <img
                        src={job.thumbnail_url}
                        alt={job.title || 'Video'}
                        className="w-full h-full object-cover"
                      />
                    )}
                    {!job.thumbnail_url && (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-4xl">🎬</span>
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <p className="font-semibold mb-2 truncate">
                    {job.title || 'Untitled Video'}
                  </p>
                  <p className="text-sm text-gray-400 mb-3 line-clamp-2 min-h-10">
                    {job.description || job.topic}
                  </p>

                  {/* Tags */}
                  {job.tags && job.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {job.tags.slice(0, 2).map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-primary-500/20 rounded text-xs text-primary-300"
                        >
                          #{tag}
                        </span>
                      ))}
                      {job.tags.length > 2 && (
                        <span className="px-2 py-1 bg-primary-500/20 rounded text-xs text-primary-300">
                          +{job.tags.length - 2}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Date + Delete */}
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      {formatDate(job.created_at)}
                    </p>
                    <button
                      onClick={(e) => handleDelete(e, job.id)}
                      className="text-xs text-gray-500 hover:text-red-400 transition-colors px-2 py-1"
                      title="Delete video"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-5xl mb-4">🎬</p>
            <h3 className="text-2xl font-bold mb-2">No videos yet</h3>
            <p className="text-gray-400 mb-8">
              Create your first video to get started!
            </p>
            <button
              onClick={() => router.push('/create')}
              className="button-primary"
            >
              Create Your First Video
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
