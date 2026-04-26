import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { Navbar } from '@/components/Navbar'
import { Footer } from '@/components/Footer'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ClipPilot Lite - AI Short Video Generator',
  description:
    'Turn any topic into a professional short vertical video in minutes with AI-powered research, narration, and editing.',
  keywords: [
    'short video',
    'AI video',
    'vertical video',
    'video generator',
    'content creation',
  ],
  openGraph: {
    title: 'ClipPilot Lite - AI Short Video Generator',
    description:
      'Turn any topic into a professional short vertical video in minutes.',
    type: 'website',
    images: [
      {
        url: 'https://clippilot.vercel.app/og-image.png',
        width: 1200,
        height: 630,
        alt: 'ClipPilot Lite',
      },
    ],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body
        className={`${inter.className} bg-dark-bg text-white flex flex-col min-h-screen`}
      >
        <Navbar />
        <main className="flex-1">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  )
}
