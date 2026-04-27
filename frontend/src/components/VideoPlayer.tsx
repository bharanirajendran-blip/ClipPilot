'use client'

import { useRef, useState, useEffect, useCallback } from 'react'

interface VideoPlayerProps {
  videoUrl: string
  poster?: string
}

const formatTime = (seconds: number): string => {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export const VideoPlayer = ({ videoUrl, poster }: VideoPlayerProps) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const progressRef = useRef<HTMLDivElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isSeeking, setIsSeeking] = useState(false)
  const [volume, setVolume] = useState(1)
  const [isMuted, setIsMuted] = useState(false)

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  // Update progress bar as video plays
  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleTimeUpdate = () => {
      if (!isSeeking && video.duration) {
        setProgress((video.currentTime / video.duration) * 100)
        setCurrentTime(video.currentTime)
      }
    }

    const handleLoadedMetadata = () => {
      setDuration(video.duration)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setProgress(0)
      setCurrentTime(0)
    }

    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)

    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('loadedmetadata', handleLoadedMetadata)
    video.addEventListener('ended', handleEnded)
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      video.removeEventListener('ended', handleEnded)
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
    }
  }, [isSeeking])

  // Seek handler — works for click and drag
  const seekTo = useCallback((e: React.MouseEvent | MouseEvent) => {
    const bar = progressRef.current
    const video = videoRef.current
    if (!bar || !video || !video.duration) return

    const rect = bar.getBoundingClientRect()
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width))
    const pct = x / rect.width
    video.currentTime = pct * video.duration
    setProgress(pct * 100)
    setCurrentTime(video.currentTime)
  }, [])

  const handleSeekStart = (e: React.MouseEvent) => {
    setIsSeeking(true)
    seekTo(e)

    const handleMove = (ev: MouseEvent) => seekTo(ev)
    const handleUp = () => {
      setIsSeeking(false)
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('mouseup', handleUp)
    }

    window.addEventListener('mousemove', handleMove)
    window.addEventListener('mouseup', handleUp)
  }

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  return (
    <div className="video-container rounded-lg overflow-hidden shadow-2xl max-w-sm mx-auto" style={{ aspectRatio: '9/16' }}>
      <div className="relative w-full h-full flex items-center justify-center bg-black group">
        <video
          ref={videoRef}
          src={videoUrl}
          poster={poster}
          className="w-full h-full object-contain"
          controlsList="nodownload"
          playsInline
          onClick={togglePlay}
        />

        {/* Custom Play Button Overlay — shown when paused */}
        {!isPlaying && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 flex items-center justify-center bg-black/30 group-hover:bg-black/40 transition-all"
          >
            <div className="bg-white rounded-full p-6 shadow-lg transform group-hover:scale-110 transition-transform">
              <svg
                className="w-8 h-8 text-black fill-current"
                viewBox="0 0 24 24"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </button>
        )}

        {/* Controls Bar */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity">
          {/* Seek Bar */}
          <div
            ref={progressRef}
            onMouseDown={handleSeekStart}
            className="w-full h-2 bg-white/20 rounded-full cursor-pointer mb-3 group/seek hover:h-3 transition-all"
          >
            <div
              className="h-full bg-primary-500 rounded-full relative"
              style={{ width: `${progress}%` }}
            >
              {/* Seek handle */}
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow opacity-0 group-hover/seek:opacity-100 transition-opacity" />
            </div>
          </div>

          {/* Controls Row */}
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="text-white hover:text-primary-400 transition-colors text-lg"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>

            {/* Time Display */}
            <span className="text-white/70 text-xs font-mono min-w-[70px]">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>

            <div className="flex-1" />

            {/* Volume */}
            <button
              onClick={toggleMute}
              className="text-white hover:text-primary-400 transition-colors"
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? '🔇' : '🔊'}
            </button>

            {/* Fullscreen */}
            <button
              onClick={() => {
                if (videoRef.current) {
                  videoRef.current.requestFullscreen()
                }
              }}
              className="text-white hover:text-primary-400 transition-colors"
              title="Fullscreen"
            >
              ⛶
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
