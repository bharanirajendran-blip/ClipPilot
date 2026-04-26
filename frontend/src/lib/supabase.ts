import { createClient as createSupabaseClient, SupabaseClient } from '@supabase/supabase-js'

let supabaseInstance: SupabaseClient | null = null

export const createClient = () => {
  if (supabaseInstance) return supabaseInstance

  supabaseInstance = createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
    {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        storageKey: 'clippilot-auth',
        flowType: 'implicit',
      },
    }
  )

  return supabaseInstance
}

export type Database = {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          email: string
          videos_remaining: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          videos_remaining?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          videos_remaining?: number
          updated_at?: string
        }
      }
      jobs: {
        Row: {
          id: string
          user_id: string
          topic: string
          style: string
          duration: number
          status: 'queued' | 'pending' | 'processing' | 'completed' | 'failed'
          progress: number
          current_step: string
          video_url: string | null
          title: string | null
          description: string | null
          tags: string[] | null
          thumbnail_url: string | null
          error_message: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          topic: string
          style: string
          duration: number
          status?: 'queued' | 'pending'
          progress?: number
          current_step?: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          status?: 'queued' | 'processing' | 'completed' | 'failed'
          progress?: number
          current_step?: string
          video_url?: string
          title?: string
          description?: string
          tags?: string[]
          thumbnail_url?: string
          error_message?: string
          updated_at?: string
        }
      }
    }
    Views: {}
    Functions: {}
    Enums: {}
  }
}
