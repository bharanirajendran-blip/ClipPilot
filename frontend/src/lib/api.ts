export interface Job {
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

export interface JobStatusResponse {
  status: 'queued' | 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  current_step: string
  error_message?: string
}

export interface JobResultResponse {
  video_url: string
  title: string
  description: string
  tags: string[]
  thumbnail_url: string
  research_data?: any
  script_data?: any
  shot_list_data?: any
}

export interface UserProfile {
  id: string
  email: string
  videos_remaining: number
  created_at: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const getHeaders = (token: string): HeadersInit => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`,
})

export const apiClient = {
  async uploadAudio(token: string, file: File): Promise<{ audio_url: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_URL}/api/jobs/upload-audio`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error(
        `Failed to upload audio: ${response.status} ${response.statusText}`
      )
    }

    return response.json()
  },

  async createJob(
    token: string,
    topic: string,
    style: string,
    duration: number,
    audio_url?: string
  ): Promise<{ job_id: string }> {
    const body: any = {
      topic,
      style,
      duration,
    }

    if (audio_url) {
      body.audio_url = audio_url
    }

    const response = await fetch(`${API_URL}/api/jobs`, {
      method: 'POST',
      headers: getHeaders(token),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(
        `Failed to create job: ${response.status} ${response.statusText}`
      )
    }

    return response.json()
  },

  async getJobStatus(token: string, jobId: string): Promise<JobStatusResponse> {
    const response = await fetch(`${API_URL}/api/jobs/${jobId}/status`, {
      method: 'GET',
      headers: getHeaders(token),
    })

    if (!response.ok) {
      throw new Error(
        `Failed to get job status: ${response.status} ${response.statusText}`
      )
    }

    return response.json()
  },

  async getJobResult(token: string, jobId: string): Promise<JobResultResponse> {
    const response = await fetch(`${API_URL}/api/jobs/${jobId}/result`, {
      method: 'GET',
      headers: getHeaders(token),
    })

    if (!response.ok) {
      throw new Error(
        `Failed to get job result: ${response.status} ${response.statusText}`
      )
    }

    return response.json()
  },

  async getUserJobs(token: string): Promise<Job[]> {
    const response = await fetch(`${API_URL}/api/jobs`, {
      method: 'GET',
      headers: getHeaders(token),
    })

    if (!response.ok) {
      throw new Error(
        `Failed to get user jobs: ${response.status} ${response.statusText}`
      )
    }

    const data = await response.json()
    return data.jobs || []
  },

  async getUserProfile(token: string): Promise<UserProfile> {
    const response = await fetch(`${API_URL}/api/profile`, {
      method: 'GET',
      headers: getHeaders(token),
    })

    if (!response.ok) {
      throw new Error(
        `Failed to get user profile: ${response.status} ${response.statusText}`
      )
    }

    return response.json()
  },

  async cancelJob(token: string, jobId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/jobs/${jobId}/cancel`, {
      method: 'POST',
      headers: getHeaders(token),
    })

    if (!response.ok) {
      throw new Error(
        `Failed to cancel job: ${response.status} ${response.statusText}`
      )
    }
  },

  async deleteJob(token: string, jobId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
      method: 'DELETE',
      headers: getHeaders(token),
    })

    if (!response.ok) {
      throw new Error(
        `Failed to delete job: ${response.status} ${response.statusText}`
      )
    }
  },
}
