'use client'

import { useState, useEffect } from 'react'
import { useAuth, useRedirectIfNotAuth } from '@/lib/hooks'
import { useRouter } from 'next/navigation'
import { apiClient } from '@/lib/api'

type StyleType = 'educational' | 'storytelling' | 'explainer' | 'documentary' | 'animated'
type DurationType = 30 | 60 | 90

const topicSuggestions: Record<string, { icon: string; topics: string[] }> = {
  'Science & Nature': {
    icon: '🔬',
    topics: [
      'How black holes form and what happens at the event horizon',
      'The secret life of deep ocean creatures in the midnight zone',
      'How CRISPR gene editing is revolutionizing medicine',
      'Why do volcanoes erupt? The geology beneath our feet',
    ],
  },
  'History & Culture': {
    icon: '🏛️',
    topics: [
      'The rise and fall of the Roman Empire in 60 seconds',
      'How ancient Egyptians built the pyramids without modern tools',
      'The history of coffee from Ethiopia to your morning cup',
      'Silk Road: the trade route that connected civilizations',
    ],
  },
  'Technology & AI': {
    icon: '🤖',
    topics: [
      'How large language models like ChatGPT actually work',
      'The evolution of smartphones from 2007 to today',
      'Blockchain explained simply: beyond cryptocurrency',
      'How self-driving cars see and navigate the world',
    ],
  },
  'Health & Psychology': {
    icon: '🧠',
    topics: [
      'Why do we dream? The neuroscience of sleep explained',
      'How exercise physically changes your brain structure',
      'The gut-brain connection: your second brain explained',
      'What happens to your body during a 24-hour fast',
    ],
  },
}

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
    type="button"
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
  const [activeCategory, setActiveCategory] = useState<string | null>(null)
  const [style, setStyle] = useState<StyleType>('educational')
  const [duration, setDuration] = useState<DurationType>(30)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [videosRemaining, setVideosRemaining] = useState<number | null>(null)
  const [loadingProfile, setLoadingProfile] = useState(true)
  const [musicFile, setMusicFile] = useState<File | null>(null)
  const [musicUrl, setMusicUrl] = useState<string | null>(null)
  const [musicUploading, setMusicUploading] = useState(false)
  const [musicError, setMusicError] = useState<string | null>(null)
  const [includeNarration, setIncludeNarration] = useState(true)
  const [includeCaptions, setIncludeCaptions] = useState(true)
  const [includeMusic, setIncludeMusic] = useState(true)

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

  const handleMusicSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setMusicFile(file)
    setMusicError(null)
    setMusicUploading(true)

    try {
      if (!session?.access_token) {
        throw new Error('You must be logged in to upload music')
      }

      const response = await apiClient.uploadMusic(session.access_token, file)
      setMusicUrl(response.music_url)
    } catch (err) {
      const errorMessage = friendlyError(err)
      setMusicError(errorMessage)
      setMusicFile(null)
    } finally {
      setMusicUploading(false)
    }
  }

  const handleRemoveMusic = () => {
    setMusicFile(null)
    setMusicUrl(null)
    setMusicError(null)
  }

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
        {
          include_narration: includeNarration,
          include_captions: includeCaptions,
          include_music: includeMusic,
          music_url: musicUrl || undefined,
        }
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

            {/* Subject Category Chips */}
            <div className="mb-4">
              <div className="flex flex-wrap gap-2 mb-3">
                {Object.entries(topicSuggestions).map(([category, { icon }]) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => setActiveCategory(activeCategory === category ? null : category)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      activeCategory === category
                        ? 'bg-primary-500 text-white'
                        : 'bg-dark-surface border border-dark-border text-gray-300 hover:border-primary-500/50 hover:text-white'
                    }`}
                  >
                    {icon} {category}
                  </button>
                ))}
              </div>

              {/* Suggestion Topics */}
              {activeCategory && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
                  {topicSuggestions[activeCategory].topics.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => {
                        setTopic(suggestion)
                        setTopicTouched(true)
                        setActiveCategory(null)
                      }}
                      className="text-left p-3 text-sm text-primary-300 bg-primary-500/5 border border-primary-500/20 rounded-lg hover:bg-primary-500/10 hover:border-primary-500/40 transition-all"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>

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
                id="documentary"
                title="Documentary"
                description="In-depth exploration with rich visuals"
                icon="🎥"
                selected={style === 'documentary'}
                onClick={() => setStyle('documentary')}
              />
              <StyleCard
                id="animated"
                title="Animated"
                description="Colorful cartoon-style visuals, great for abstract topics"
                icon="🎨"
                selected={style === 'animated'}
                onClick={() => setStyle('animated')}
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

          {/* Audio & Visual Options */}
          <div>
            <label className="block text-lg font-semibold mb-4">Audio & Visual Options</label>
            <div className="space-y-3">
              {/* Narration Toggle */}
              <label className="flex items-center justify-between p-4 bg-dark-surface border border-dark-border rounded-lg cursor-pointer hover:border-primary-500/30 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="text-xl">🎙️</span>
                  <div>
                    <p className="font-medium text-gray-200">AI Narration</p>
                    <p className="text-xs text-gray-500">ElevenLabs voiceover for your script</p>
                  </div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={includeNarration}
                  onClick={() => setIncludeNarration(!includeNarration)}
                  className={`relative w-12 h-7 rounded-full transition-colors ${
                    includeNarration ? 'bg-primary-500' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full transition-transform ${
                      includeNarration ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </label>

              {/* Captions Toggle */}
              <label className="flex items-center justify-between p-4 bg-dark-surface border border-dark-border rounded-lg cursor-pointer hover:border-primary-500/30 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="text-xl">💬</span>
                  <div>
                    <p className="font-medium text-gray-200">Captions</p>
                    <p className="text-xs text-gray-500">Burned-in subtitles on the video</p>
                  </div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={includeCaptions}
                  onClick={() => setIncludeCaptions(!includeCaptions)}
                  className={`relative w-12 h-7 rounded-full transition-colors ${
                    includeCaptions ? 'bg-primary-500' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full transition-transform ${
                      includeCaptions ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </label>

              {/* Music Toggle */}
              <label className="flex items-center justify-between p-4 bg-dark-surface border border-dark-border rounded-lg cursor-pointer hover:border-primary-500/30 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="text-xl">🎵</span>
                  <div>
                    <p className="font-medium text-gray-200">Background Music</p>
                    <p className="text-xs text-gray-500">
                      {includeNarration
                        ? 'Soft ambient music under narration'
                        : 'Music-only soundtrack (no voice)'}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={includeMusic}
                  onClick={() => setIncludeMusic(!includeMusic)}
                  className={`relative w-12 h-7 rounded-full transition-colors ${
                    includeMusic ? 'bg-primary-500' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full transition-transform ${
                      includeMusic ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </label>

              {/* Custom Music Upload — shown when music is enabled */}
              {includeMusic && (
                <div className="ml-10 p-4 bg-dark-surface/50 border border-dark-border/60 rounded-lg">
                  <p className="text-sm text-gray-400 mb-3">
                    Upload your own MP3, or leave blank for auto-generated ambient music matched to your style.
                  </p>
                  {!musicUrl ? (
                    <label className="flex items-center justify-center gap-3 p-4 border-2 border-dashed border-dark-border rounded-lg cursor-pointer hover:border-primary-500/50 transition-colors group">
                      <div className="text-center">
                        <div className="text-2xl mb-1 group-hover:scale-110 transition-transform">📁</div>
                        <p className="text-gray-400 font-semibold text-sm">Upload Music</p>
                        <p className="text-xs text-gray-500 mt-1">MP3, WAV, or M4A</p>
                      </div>
                      <input
                        type="file"
                        accept=".mp3,.wav,.m4a"
                        onChange={handleMusicSelect}
                        disabled={isSubmitting || musicUploading || videosRemaining === 0}
                        className="hidden"
                      />
                    </label>
                  ) : (
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-200 flex items-center gap-2 text-sm">
                          ✓ {musicFile?.name || 'Custom music'}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Your music will be used as the background track
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={handleRemoveMusic}
                        className="px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm hover:bg-red-500/30 transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                  {musicUploading && (
                    <p className="text-center text-gray-400 mt-3 text-sm">
                      Uploading music...
                    </p>
                  )}
                  {musicError && (
                    <p className="text-center text-red-400 mt-3 text-sm">
                      {musicError}
                    </p>
                  )}
                </div>
              )}

              {/* Warning when both narration and music are off */}
              {!includeNarration && !includeMusic && (
                <p className="text-yellow-400 text-sm px-1">
                  Your video will have no audio. Consider enabling at least background music.
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

          {/* How It Works */}
          <div className="p-6 bg-dark-surface border border-dark-border rounded-lg">
            <h3 className="font-semibold mb-4 flex items-center gap-2 text-lg">
              🎬 How It Works
            </h3>
            <ul className="space-y-3 text-gray-400 text-sm">
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">1.</span>
                <span>
                  <strong className="text-gray-200">Research:</strong> AI researches your topic for accurate, up-to-date facts
                </span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">2.</span>
                <span>
                  <strong className="text-gray-200">Script:</strong> A narration script is written and reviewed by AI agents
                </span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">3.</span>
                <span>
                  <strong className="text-gray-200">Generate:</strong> Video scenes, voice narration, and captions are created
                </span>
              </li>
              <li className="flex gap-3">
                <span className="text-primary-400 font-bold">4.</span>
                <span>
                  <strong className="text-gray-200">Assemble:</strong> Everything is stitched into a polished short video
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
