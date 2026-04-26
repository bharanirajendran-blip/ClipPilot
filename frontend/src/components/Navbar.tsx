'use client'

import { useAuth } from '@/lib/hooks'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export const Navbar = () => {
  const { user, signOut } = useAuth()
  const router = useRouter()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleSignOut = async () => {
    try {
      await signOut()
      setShowUserMenu(false)
    } catch (err) {
      console.error('Sign out failed:', err)
    }
  }

  return (
    <nav className="border-b border-dark-border bg-dark-surface/50 backdrop-blur sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl">🎬</span>
            <span className="font-bold text-lg hidden sm:inline">
              <span className="text-gradient">ClipPilot</span>
              <span className="text-gray-400 text-sm ml-2">Lite</span>
            </span>
            <span className="font-bold text-lg sm:hidden">CP</span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-1 sm:gap-4">
            {user && (
              <>
                <Link
                  href="/create"
                  className="px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-dark-border transition-colors text-sm sm:text-base"
                >
                  Create
                </Link>
                <Link
                  href="/dashboard"
                  className="px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-dark-border transition-colors text-sm sm:text-base"
                >
                  Dashboard
                </Link>
              </>
            )}
          </div>

          {/* Auth Section */}
          <div className="flex items-center gap-4">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="px-3 py-2 rounded-lg bg-dark-border hover:bg-dark-border/80 transition-colors text-sm flex items-center gap-2"
                >
                  <span className="hidden sm:inline text-gray-300">
                    {user.email?.split('@')[0]}
                  </span>
                  <span className="text-lg">👤</span>
                </button>

                {/* User Menu */}
                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-dark-surface border border-dark-border rounded-lg shadow-lg overflow-hidden animate-slide-in">
                    <div className="px-4 py-3 border-b border-dark-border">
                      <p className="text-sm text-gray-400">Signed in as</p>
                      <p className="text-white font-semibold truncate">
                        {user.email}
                      </p>
                    </div>
                    <button
                      onClick={handleSignOut}
                      className="w-full text-left px-4 py-2 text-gray-300 hover:bg-dark-border transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => router.push('/auth')}
                className="button-primary text-sm"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
