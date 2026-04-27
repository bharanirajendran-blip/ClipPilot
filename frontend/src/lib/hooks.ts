'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Session, User } from '@supabase/supabase-js'
import { createClient } from './supabase'
import { apiClient, JobStatusResponse } from './api'

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const getSession = async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession()
        setSession(session)
        setUser(session?.user ?? null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get session')
      } finally {
        setLoading(false)
      }
    }

    getSession()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    return () => {
      subscription?.unsubscribe()
    }
  }, [])

  const signUp = useCallback(
    async (email: string, password: string) => {
      try {
        setError(null)
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
        })

        if (error) throw error
        return data
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Sign up failed'
        setError(message)
        throw err
      }
    },
    [supabase]
  )

  const signIn = useCallback(
    async (email: string, password: string) => {
      try {
        setError(null)
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })

        if (error) throw error
        return data
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Sign in failed'
        setError(message)
        throw err
      }
    },
    [supabase]
  )

  const signOut = useCallback(async () => {
    try {
      setError(null)
      await supabase.auth.signOut()
      setUser(null)
      setSession(null)
      router.push('/')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Sign out failed'
      setError(message)
      throw err
    }
  }, [supabase, router])

  return {
    user,
    session,
    loading,
    error,
    signUp,
    signIn,
    signOut,
  }
}

export const useJobPolling = (
  jobId: string | null,
  initialStatus?: JobStatusResponse['status']
) => {
  const [status, setStatus] = useState<JobStatusResponse | null>(
    initialStatus ? { status: initialStatus, progress: 0, current_step: '' } : null
  )
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { session } = useAuth()

  useEffect(() => {
    if (!jobId || !session?.access_token) {
      setLoading(false)
      return
    }

    const pollStatus = async () => {
      try {
        const jobStatus = await apiClient.getJobStatus(
          session.access_token,
          jobId
        )
        setStatus(jobStatus)
        setError(null)
        setLoading(false)
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to poll job status'
        setError(message)
        setLoading(false)
      }
    }

    pollStatus()

    let interval: NodeJS.Timeout | null = null
    if (!status || (status.status !== 'completed' && status.status !== 'failed')) {
      interval = setInterval(pollStatus, 3000)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [jobId, session?.access_token, status?.status])

  return {
    status,
    loading,
    error,
  }
}

export const useRedirectIfNotAuth = () => {
  const router = useRouter()
  const { user, loading } = useAuth()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth')
    }
  }, [user, loading, router])

  return { user, loading }
}
