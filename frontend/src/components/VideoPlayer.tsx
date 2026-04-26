'use client'

import { useRef, useState } from 'react'

interface VideoPlayerProps {
  videoUrl: string
  poster?: string
}

export const VideoPlayer = ({ videoUrl, poster }: VideoPlayerProps) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)

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

  return (
    <div className="video-container aspect-video rounded-lg overflow-hidden shadow-2xl max-w-full">
      <div className="relative w-full h-full flex items-center justify-center bg-black group">
        <video
          ref={videoRef}
          src={videoUrl}
          poster={poster}
          className="w-full h-full object-cover"
          controlsList="nodownload"
        />

        {/* Custom Play Button Overlay */}
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

        {/* Controls */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="text-white hover:text-primary-400 transition-colors"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>
            <div className="flex-1 h-1 bg-white/20 rounded-full cursor-pointer hover:bg-white/30">
              <div className="h-full bg-primary-500 rounded-full" />
            </div>
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
