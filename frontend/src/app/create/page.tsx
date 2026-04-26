'use client'

import { useState, useEffect } from 'react'
import { useAuth, useRedirectIfNotAuth } from '@/lib/hooks'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api'

type StyleType = 'educational' | 'storytelling' | 'explainer' | 'news'
type DurationType = 30 | 60 | 90

// Helper to map API errors to user-friendly messages
const friendlyError = (error: unknown): string => {
  const message = error instanceof Error ? error.message : String(error)

  // Check for HTTP status codes in the error message
  if (message.includes('429')) {
    return "You've reached your video limit."
  }
  if (message.includes('503') || message.includes('Service Unavailable')) {
    return 'Our servers are busy. Please try again shortly.'
  }
  if (message.includes('network') || message.includes('Network')) {
    return 'Unable to connect. Please check your internet connection.'
  }
  if (message.includes('fetch') || message.includes('Failed to fetch')) {
    return 'Unable to connect. Please check your internet connection.'
  }
  // Default fallback without exposing raw error text
  return 'Something went wrong. Please try again.'
}

const StyleCard = ({
  id,
  title,
  description,
  icon,
  selected,
  onClick,
}: {
  id: StyleType
  title: string
  description: string
  icon: string
  selected: boolean
  onClick: () => void
}) => (
  <button
    onClick={onClick}
    className={`p-6 rounded-lg border-2 transition-all text-left ${
      selected
        ? 'border-primary-500 bg-primary-500/10'
        : 'border-dark-border bg-dark-surface hover:border-primary-500/50'
    }`}
  >
    <div className="text-3xl mb-3">{icon}</div>
    <h3 className="font-semibold text-lg mb-1">{title}</h3>
    <p className="text-sm text-gray-400">{description}</p>
  </button>
)

export default function CreatePage() {
  const { user, loading } = useRedirectIfNotAuth()
  const { session } = useAuth()
  const router = useRouter()

  const [topic, setTopic] = useState('')
  const [topicTouched, setTopicTouched] = useState(false)
  const [style, setStyle] = useState<StyleType>('educational')
  const [duration, setDuration] = useState<DurationType>(30)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [videosRemaining, setVideosRemaining] = useState<number | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [audioUploading, setAudioUploading] = useState(false)
  const [audioError, setAudioError] = useState<string | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null)

  // Fetch user profile to get videos remaining
  useEffect(() => {
    const fetchProfile = async () => {
      if (!session?.access_token) return

      try {
        const profile = await apiClient.getUserProfile(session.access_token)
        setVideosRemaining(profile.videos_remaining)
      } catch (err) {
        console.error('Failed to fetch profile:', err)
      } finally {
        setLoadingProfile(false)
      }
    }

    fetchProfile()
  }, [session?.access_token])

  const handleAudioSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setAudioFile(file)
    setAudioError(null)
    setAudioUploading(true)

    try {
      if (!session?.access_token) {
        throw new Error('You must be logged in to upload audio')
      }

      const response = await apiClient.uploadAudio(session.access_token, file)
      setAudioUrl(response.audio_url)
    } catch (err) {
      const errorMessage = friendlyError(err)
      setAudioError(errorMessage)
      setAudioFile(null)
    } finally {
      setAudioUploading(false)
    }
  }

  const handleRemoveAudio = () => {
    setAudioFile(null)
    setAudioUrl(null)
    setAudioError(null)
    setIsRecording(false)
    setRecordingTime(0)
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    setMediaRecorder(null)
  }

  const startRecording = async () => {
    try {
      setAudioError(null)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      const chunks: BlobPart[] = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop())
        const blob = new Blob(chunks, { type: 'audio/webm' })
        const file = new File([blob], `recording-${Date.now()}.webm`, {
          type: 'audio/webm',
        })

        setAudioFile(file)
        setAudioUploading(true)

        try {
          if (!session?.access_token) {
            throw new Error('You must be logged in to record audio')
          }
          const response = await apiClient.uploadAudio(
            session.access_token,
            file
          )
          setAudioUrl(response.audio_url)
        } catch (err) {
          const errorMessage = friendlyError(err)
          setAudioError(errorMessage)
          setAudioFile(null)
        } finally {
          setAudioUploading(false)
        }
      }

      recorder.start()
      setMediaRecorder(recorder)
      setIsRecording(true)
      setRecordingTime(0)
    } catch (err) {
      setAudioError(
        'Microphone access denied. Please allow microphone access in your browser settings.'
      )
    }
  }

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    setIsRecording(false)
  }

  // Recording timer
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null
    if (isRecording) {
      timer = setInterval(() => setRecordingTime((t) => t + 1), 1000)
    }
    return () => {
      if (timer) clearInterval(timer)
    }
  }, [isRecording])

  const isTopicValid = topic.trim().length >= 10
  const isTopicTooLong = topic.length > 500

  const handleTopicChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setTopic(e.target.value.slice(0, 500))
    if (!topicTouched && e.target.value.length > 0) {
      setTopicTouched(true)
    }
  }

  const handleTopicBlur = () => {
    if (topic.length > 0) {
      setTopicTouched(true)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!topic.trim() || topic.trim().length < 10) {
      setError('Please enter a topic with at least 10 characters')
      return
    }

    if (!session?.access_token) {
      setError('You must be logged in to create a video')
      return
    }

    if (videosRemaining === 0) {
      setError('You have no remaining videos. Upgrade to create more.')
      return
    }

    setIsSubmitting(true)

    try {
      const result = await apiClient.createJob(
        session.access_token,
        topic,
        style,
        duration,
        audioUrl || undefined
      )

      router.push(`/status/${result.job_id}`)
    } catch (err) {
      const errorMessage = friendlyError(err)
      setError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loading || loadingProfile) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin mb-4">
            <div className="text-4xl">⚙️</div>
          </div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-dark py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Create Your Video
          </h1>
          <p className="text-xl text-gray-400">
            Tell us what you want to create, and AI will handle the rest.
          </p>
        </div>

        {/* Videos Remaining Counter */}
        <div className="mb-8 p-6 bg-primary-500/10 border border-primary-500/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-1">Videos remaining</p>
              <p className="text-3xl font-bold text-gradient">
                {videosRemaining === null ? '-' : videosRemaining}
              </p>
            </div>
            <div className="text-5xl">🎬</div>
          </div>
        </div>

        {/* Main Form — onSubmit only fires from the Generate button, not Enter key */}
        <form onSubmit={handleSubmit} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) e.preventDefault() }} className="space-y-8">
          {/* Topic Input */}
          <div>
            <label htmlFor="topic" className="block text-lg font-semibold mb-3">
              What's your topic?
            </label>
            <p className="text-gray-400 mb-4 text-sm">
              Describe what you want your video to be about. Be specific or
              general—our AI adapts.
            </p>
            <textarea
              id="topic"
              required
              disabled={isSubmitting || videosRemaining === 0}
              value={topic}
              onChange={handleTopicChange}
              onBlur={handleTopicBlur}
              placeholder="e.g., The history of artificial intelligence, how photosynthesis works, the benefits of meditation..."
              maxLength={500}
              rows={5}
              className={`input-base resize-none transition-colors ${
                topicTouched && topic.length > 0
                  ? isTopicValid
                    ? 'border-green-500/30'
                    : 'border-red-500/30'
                  : ''
              }`}
            />
            {/* Validation Message */}
            {topicTouched && topic.length > 0 && !isTopicValid && (
              <p className="text-red-400 text-sm mt-2">
                Topic must be at least 10 characters
              </p>
            )}
            {topicTouched && isTopicValid && (
              <p className="text-green-400 text-sm mt-2">✓ Valid topic</p>
            )}
            {/* Character Counter */}
            <div className="flex justify-end mt-2">
              <p
                className={`text-xs font-mono ${
                  topicTouched && topic.length > 0
                    ? topic.length > 450
                      ? 'text-red-400'
                      : 'text-gray-500'
                    : 'text-gray-500'
                }`}
              >
                {topic.length} / 500
              </p>
            </div>
          </div>

          {/* Style Selection */}
          <div>
            <label className="block text-lg font-semibold mb-4">
              Choose your style
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <StyleCard
                id="educational"
                title="Educational"
                description="Informative and structured for learning"
                icon="📚"
                selected={style === 'educational'}
                onClick={() => setStyle('educational')}
              />
              <StyleCard
                id="storytelling"
                title="Storytelling"
                description="Engaging narrative-driven content"
                icon="📖"
                selected={style === 'storytelling'}
                onClick={() => setStyle('storytelling')}
              />
              <StyleCard
                id="explainer"
                title="Explainer"
                description="Clear, concise how-to videos"
                icon="💡"
                selected={style === 'explainer'}
                onClick={() => setStyle('explainer')}
              />
              <StyleCard
                id="news"
                title="News"
                description="Quick facts and current events"
                icon="📰"
                selected={style === 'news'}
                onClick={() => setStyle('news')}
              />
            </div>
          </div>

          {/* Duration Selection */}
          <div>
            <label className="block text-lg font-semibold mb-4">Duration</label>
            <div className="flex gap-4">
              {[30, 60, 90].map((dur) => (
                <button
                  key={dur}
                  type="button"
                  onClick={() => setDuration(dur as DurationType)}
                  className={`px-8 py-3 rounded-lg font-semibold border-2 transition-all ${
                    duration === dur
                      ? 'border-primary-500 bg-primary-500/20 text-white'
                      : 'border-dark-border bg-dark-surface text-gray-400 hover:border-primary-500/50'
                  }`}
                  disabled={isSubmitting || videosRemaining === 0}
                >
                  {dur} seconds
                </button>
              ))}
            </div>
          </div>

          {/* Audio Section — Record or Upload */}
          <div>
            <label className="block text-lg font-semibold mb-4">
              Your Own Narration (Optional)
            </label>
            <p className="text-gray-400 mb-4 text-sm">
              Record your voice or upload an audio file. If skipped, AI will generate narration.
            </p>
            <div className="p-6 bg-dark-surface border border-dark-border rounded-lg">
              {!audioUrl && !isRecording ? (
                <div className="flex flex-col sm:flex-row gap-4">
                  {/* Record Button */}
                  <button
                    type="button"
                    onClick={startRecording}
                    disabled={isSubmitting || audioUploading || videosRemaining === 0}
                    className="flex-1 flex items-center justify-center gap-3 p-6 border-2 border-dashed border-dark-border rounded-lg hover:border-red-500/50 transition-colors group"
                  >
                    <div className="text-center">
                      <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">🎤</div>
                      <p className="text-gray-400 font-semibold">Record</p>
                      <p className="text-xs text-gray-500 mt-1">Use your microphone</p>
                    </div>
                  </button>

                  {/* Upload Button */}
                  <label className="flex-1 flex items-center justify-center gap-3 p-6 border-2 border-dashed border-dark-border rounded-lg cursor-pointer hover:border-primary-500/50 transition-colors group">
                    <div className="text-center">
                      <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">📁</div>
                      <p className="text-gray-400 font-semibold">Upload File</p>
                      <p className="text-xs text-gray-500 mt-1">MP3, WAV, or M4A</p>
                    </div>
                    <input
                      type="file"
                      accept=".mp3,.wav,.m4a,.webm"
                      onChange={handleAudioSelect}
                      disabled={isSubmitting || audioUploading || videosRemaining === 0}
                      className="hidden"
                    />
                  </label>
                </div>
              ) : isRecording ? (
                <div className="text-center">
                  <div className="flex items-center justify-center gap-3 mb-4">
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-red-400 font-semibold text-lg">Recording...</span>
                    <span className="text-gray-400 font-mono">
                      {Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}
                    </span>
                  </div>
                  <div className="flex justify-center gap-4">
                    <button
                      type="button"
                      onClick={stopRecording}
                      className="px-6 py-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 hover:bg-red-500/30 transition-colors font-semibold"
                    >
                      Stop Recording
                    </button>
                    <button
                      type="button"
                      onClick={handleRemoveAudio}
                      className="px-6 py-3 bg-dark-border/50 border border-dark-border rounded-lg text-gray-400 hover:bg-dark-border transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-200 flex items-center gap-2">
                      ✓ {audioFile?.name || 'Recording'}
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      Audio ready to use
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleRemoveAudio}
                    className="px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 hover:bg-red-500/30 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              )}
              {audioUploading && (
                <p className="text-center text-gray-400 mt-3 text-sm">
                  Uploading audio...
                </p>
              )}
              {audioError && (
                <p className="text-center text-red-400 mt-3 text-sm">
                  {audioError}
                </p>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
              {error}
            </div>
          )}

          {/* No Videos Remaining */}
          {videosRemaining === 0 && (
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-yellow-400">
              You've used all your free videos. Consider upgrading to create
              more.
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting || videosRemaining === 0 || !isTopicValid}
            className="button-primary w-full text-lg py-4"
          >
            {isSubmitting
              ? 'Creating your video...'
              : videosRemaining === 0
                ? 'No Videos Remaining'
                : !isTopicValid
                  ? 'Enter Valid Topic'
                  : 'Generate Video'}
          </button>
        </form>

        {/* Prompt Tips Section */}
        <div className="mt-12 grid lg:grid-cols-2 gap-8">
          {/* Tips */}
          <div className="p-6 bg-dark-surface border border-dark-border rounded-lg">
            <h3 className="font-semibold mb-4 flex items-center gap-2 text-lg">
              💡 Tips for Great Videos
            </h3>
            <ul className="space-y-3 text-gray-400 text-sm">
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">•</span>
                <span>
                  <strong className="text-gray-200">Be specific:</strong> "How CRISPR gene editing works in cancer treatment" beats "science stuff"
                </span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">•</span>
                <span>
                  <strong className="text-gray-200">Include perspective:</strong> "Explain blockchain to a 10-year-old" gives the AI a clear angle
                </span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">•</span>
                <span>
                  <strong className="text-gray-200">Add context:</strong> "The history of coffee from Ethiopia to modern espresso" tells a story arc
                </span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">•</span>
                <span>
                  <strong className="text-gray-200">Keep it focused:</strong> One clear topic works better than trying to cover everything
                </span>
              </li>
            </ul>
          </div>

          {/* Example Prompts */}
          <div className="p-6 bg-dark-surface border border-dark-border rounded-lg">
            <h3 className="font-semibold mb-4 flex items-center gap-2 text-lg">
              ✨ Example Prompts
            </h3>
            <ul className="space-y-3 text-gray-400 text-sm">
              <li className="italic text-primary-300 pl-3 border-l border-primary-500/30">
                "How do black holes form and what happens at the event horizon"
              </li>
              <li className="italic text-primary-300 pl-3 border-l border-primary-500/30">
                "The step-by-step journey of a coffee bean from farm to your morning cup"
              </li>
              <li className="italic text-primary-300 pl-3 border-l border-primary-500/30">
                "Why do we dream? The neuroscience of sleep explained simply"
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
