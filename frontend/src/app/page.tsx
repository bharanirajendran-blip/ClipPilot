'use client'

import { useAuth } from '@/lib/hooks'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

const FeatureCard = ({
  icon,
  title,
  description,
}: {
  icon: string
  title: string
  description: string
}) => (
  <div className="card-base group">
    <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">
      {icon}
    </div>
    <h3 className="text-xl font-semibold mb-2">{title}</h3>
    <p className="text-gray-400">{description}</p>
  </div>
)

export default function Home() {
  const { user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user) {
      router.push('/create')
    }
  }, [user, router])

  return (
    <div className="min-h-screen bg-gradient-dark overflow-hidden">
      {/* Hero Section */}
      <section className="section-spacing container-padding relative">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-8 inline-block">
            <span className="px-4 py-2 bg-primary-500/10 border border-primary-500/30 rounded-full text-primary-400 text-sm font-semibold">
              ✨ AI-Powered Video Generation
            </span>
          </div>

          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            Turn any topic into a{' '}
            <span className="text-gradient">short video</span> in minutes
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 mb-8 max-w-3xl mx-auto leading-relaxed">
            ClipPilot Lite uses advanced AI to research topics, write engaging scripts, generate professional narration, and assemble polished vertical videos—all in one platform.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <button
              onClick={() => router.push('/auth')}
              className="button-primary text-lg py-4 px-8"
            >
              Get Started Free
            </button>
            <button
              onClick={() => {
                document
                  .getElementById('features')
                  ?.scrollIntoView({ behavior: 'smooth' })
              }}
              className="button-outline text-lg py-4 px-8"
            >
              Learn More
            </button>
          </div>

          {/* Hero Visual */}
          <div className="relative mt-12 mb-8">
            <div className="bg-dark-surface border border-dark-border rounded-xl p-8 h-64 md:h-80 flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-secondary-500/20 opacity-50"></div>
              <div className="relative text-6xl animate-bounce">📱</div>
            </div>
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-primary-500/20 rounded-full blur-3xl"></div>
            <div className="absolute -top-4 -left-4 w-32 h-32 bg-secondary-500/20 rounded-full blur-3xl"></div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="section-spacing container-padding bg-dark-surface/50">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-gradient mb-2">2</div>
              <p className="text-gray-400">Free videos per month</p>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-gradient mb-2">9:16</div>
              <p className="text-gray-400">Perfect vertical format</p>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-gradient mb-2">60s</div>
              <p className="text-gray-400">Max video length</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section
        id="features"
        className="section-spacing container-padding scroll-mt-20"
      >
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Everything you need to create
            </h2>
            <p className="text-xl text-gray-400">
              Powered by cutting-edge AI technology
            </p>
          </div>

          <div className="grid-responsive">
            <FeatureCard
              icon="🔍"
              title="AI Research"
              description="Automatically researches your topic and gathers the most relevant, accurate information"
            />
            <FeatureCard
              icon="🎙️"
              title="Pro Narration"
              description="High-quality AI-generated voiceovers in natural, engaging tones"
            />
            <FeatureCard
              icon="📝"
              title="Smart Scripts"
              description="Intelligent script generation optimized for engagement and comprehension"
            />
            <FeatureCard
              icon="✂️"
              title="Auto Editing"
              description="Automatic video assembly with transitions, pacing, and visual effects"
            />
            <FeatureCard
              icon="📑"
              title="Auto Captions"
              description="Accurately synced captions for better accessibility and engagement"
            />
            <FeatureCard
              icon="🎨"
              title="Visual Polish"
              description="Professional graphics, text overlays, and visual enhancements included"
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="section-spacing container-padding bg-dark-surface/50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
            How it works
          </h2>

          <div className="space-y-8">
            {[
              {
                step: '1',
                title: 'Enter Your Topic',
                description:
                  'Simply describe what you want your video to be about. Be specific or general—our AI adapts to any subject.',
              },
              {
                step: '2',
                title: 'Choose Your Style',
                description:
                  'Select from educational, storytelling, explainer, or news formats. Each style optimizes the video for its purpose.',
              },
              {
                step: '3',
                title: 'Set Duration',
                description:
                  'Choose between 30 or 60 seconds. We pack maximum impact into every second.',
              },
              {
                step: '4',
                title: 'Watch Magic Happen',
                description:
                  'Our AI researches, writes, narrates, and edits your video in real-time. Watch the progress live.',
              },
              {
                step: '5',
                title: 'Download & Share',
                description:
                  'Get your finished vertical video optimized for TikTok, Instagram Reels, YouTube Shorts, and more.',
              },
            ].map((item, idx) => (
              <div key={idx} className="flex gap-6 md:gap-8">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-gradient-primary text-white font-bold">
                    {item.step}
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-gray-400">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section-spacing container-padding">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to create amazing videos?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            2 free videos to start. No credit card required.
          </p>
          <button
            onClick={() => router.push('/auth')}
            className="button-primary text-lg py-4 px-8"
          >
            Start Creating Now
          </button>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="section-spacing container-padding bg-dark-surface/50 border-t border-dark-border">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-sm text-gray-500">
            ⚠️ This application generates AI-created content. Videos are created
            using artificial intelligence for research, narration, and editing.
            Always review generated content for accuracy before sharing publicly.
          </p>
        </div>
      </section>
    </div>
  )
}
