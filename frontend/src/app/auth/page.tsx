'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/hooks'
import { createClient } from '@/lib/supabase'
import { useRouter, useSearchParams } from 'next/navigation'

type AuthMode = 'login' | 'register' | 'reset' | 'update-password'

export default function AuthPage() {
  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const { signIn, signUp, user } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const supabase = createClient()

  // Check if we arrived via password reset link
  useEffect(() => {
    const modeParam = searchParams.get('mode')
    if (modeParam === 'update-password') {
      setMode('update-password')
    }
  }, [searchParams])

  useEffect(() => {
    // Don't auto-redirect if user is setting a new password
    if (user && mode !== 'update-password') {
      router.push('/create')
    }
  }, [user, router, mode])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      if (mode === 'update-password') {
        if (password !== confirmPassword) {
          throw new Error('Passwords do not match')
        }
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters')
        }
        const { error } = await supabase.auth.updateUser({ password })
        if (error) throw error
        setSuccess('Password updated successfully! Redirecting...')
        setPassword('')
        setConfirmPassword('')
        setTimeout(() => router.push('/create'), 1500)
      } else if (mode === 'reset') {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/auth?mode=update-password`,
        })
        if (error) throw error
        setSuccess('Password reset email sent! Check your inbox.')
        setEmail('')
      } else if (mode === 'login') {
        await signIn(email, password)
        setSuccess('Logged in successfully! Redirecting...')
        setTimeout(() => router.push('/create'), 1000)
      } else {
        if (password !== confirmPassword) {
          throw new Error('Passwords do not match')
        }
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters')
        }
        await signUp(email, password)
        setSuccess(
          'Account created! Please check your email to confirm your account.'
        )
        setEmail('')
        setPassword('')
        setConfirmPassword('')
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setMode(mode === 'login' ? 'register' : 'login')
    setError(null)
    setSuccess(null)
    setEmail('')
    setPassword('')
    setConfirmPassword('')
  }

  return (
    <div className="min-h-screen bg-gradient-dark flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">
            <span className="text-gradient">ClipPilot</span>
          </h1>
          <p className="text-gray-400">
            {mode === 'login'
              ? 'Sign in to your account'
              : mode === 'reset'
                ? 'Reset your password'
                : mode === 'update-password'
                  ? 'Set your new password'
                  : 'Create a new account'}
          </p>
        </div>

        {/* Auth Card */}
        <div className="card-base">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email (hidden in update-password mode) */}
            {mode !== 'update-password' && (
            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="input-base"
                disabled={loading}
              />
            </div>
            )}

            {/* Password (not shown in reset mode) */}
            {mode !== 'reset' && (
              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium mb-2"
                >
                  {mode === 'update-password' ? 'New Password' : 'Password'}
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  autoComplete={
                    mode === 'login' ? 'current-password' : 'new-password'
                  }
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-base"
                  disabled={loading}
                />
              </div>
            )}

            {/* Confirm Password (Register Only) */}
            {(mode === 'register' || mode === 'update-password') && (
              <div>
                <label
                  htmlFor="confirmPassword"
                  className="block text-sm font-medium mb-2"
                >
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  required
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-base"
                  disabled={loading}
                />
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
                {success}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="button-primary w-full text-center"
            >
              {loading
                ? 'Loading...'
                : mode === 'login'
                  ? 'Sign In'
                  : mode === 'reset'
                    ? 'Send Reset Email'
                    : mode === 'update-password'
                      ? 'Update Password'
                      : 'Create Account'}
            </button>
          </form>

          {/* Forgot Password Link (login mode only, hidden during password update) */}
          {mode === 'login' && (
            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={() => { setMode('reset'); setError(null); setSuccess(null); }}
                disabled={loading}
                className="text-sm text-gray-400 hover:text-primary-300 transition-colors"
              >
                Forgot your password?
              </button>
            </div>
          )}

          {/* Toggle Mode (hidden during password update) */}
          {mode !== 'update-password' && (
          <div className="mt-6 pt-6 border-t border-dark-border text-center">
            <p className="text-gray-400 mb-3">
              {mode === 'reset'
                ? 'Remember your password?'
                : mode === 'login'
                  ? "Don't have an account?"
                  : 'Already have an account?'}
            </p>
            <button
              onClick={() => { setMode(mode === 'register' ? 'login' : mode === 'reset' ? 'login' : 'register'); setError(null); setSuccess(null); setEmail(''); setPassword(''); setConfirmPassword(''); }}
              disabled={loading}
              className="text-primary-400 hover:text-primary-300 font-semibold transition-colors"
            >
              {mode === 'reset' ? 'Back to Sign In' : mode === 'login' ? 'Create one here' : 'Sign in instead'}
            </button>
          </div>
          )}
        </div>

        {/* Info */}
        <div className="mt-8 p-4 bg-dark-surface/50 border border-dark-border rounded-lg text-center text-sm text-gray-400">
          <p>
            👤 Secure authentication powered by Supabase. Your data is encrypted
            and protected.
          </p>
        </div>
      </div>
    </div>
  )
}
