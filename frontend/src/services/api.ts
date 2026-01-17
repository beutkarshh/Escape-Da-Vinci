import axios from 'axios'
import { supabase } from '@/integrations/supabase/client'
import { config } from '@/config'

// Dev-auth bypass is enabled only when devAuth is true in config
const USE_DEV_AUTH = config.devAuth

// Detect if running in production or development
const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 3 minutes - orchestrator needs time for multiple AI agent calls
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token if available (skip in dev-auth mode)
if (!USE_DEV_AUTH) {
  api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
    return config
  })
}

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export interface PatientData {
  patientId: string
  age: number
  gender: string
  symptoms: string
  medicalHistory: string
  currentMedications: string
  urgency: string
}

export interface AnalysisResult {
  agentName: string
  status: string
  result: any
  timestamp: string
}

// Main analysis endpoint
export const analyzePatientCase = async (patientData: PatientData) => {
  const response = await api.post('/analyze', patientData)
  return response.data
}

// Generate PDF report
export const generatePdfReport = async (analysisPayload: any) => {
  const response = await api.post('/generate-pdf', analysisPayload, {
    responseType: 'blob'
  })
  return response.data as Blob
}

// Individual agent endpoints (aligned with backend FastAPI routes)
export const callSymptomAgent = async (payload: Partial<PatientData>) => {
  const response = await api.post('/symptom-analyzer', payload)
  return response.data
}

export const callLiteratureAgent = async (payload: Partial<PatientData>) => {
  const response = await api.post('/literature', payload)
  return response.data
}

export const callCaseAgent = async (payload: Partial<PatientData>) => {
  const response = await api.post('/case-matcher', payload)
  return response.data
}

export const callTreatmentAgent = async (payload: Partial<PatientData>) => {
  const response = await api.post('/treatment', payload)
  return response.data
}

export const callSummaryAgent = async (payload: Partial<PatientData>) => {
  const response = await api.post('/summary', payload)
  return response.data
}

// Auth functions using Supabase
export const loginUser = async (email: string, password: string) => {
  if (USE_DEV_AUTH) {
    const name = email?.split?.('@')?.[0] || 'Dev User'
    return {
      user: { id: 'dev-user-1', email, name },
      session: null as any
    }
  }
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  
  if (error) throw error
  
  return {
    user: {
      id: data.user!.id,
      email: data.user!.email!,
      name: data.user!.user_metadata?.name || data.user!.email!.split('@')[0]
    },
    session: data.session
  }
}

export const signupUser = async (email: string, password: string, name: string) => {
  if (USE_DEV_AUTH) {
    return {
      user: { id: 'dev-user-1', email, name: name || (email?.split?.('@')?.[0] || 'Dev User') },
      session: null as any
    }
  }
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        name: name,
      },
      emailRedirectTo: `${window.location.origin}/`
    }
  })
  
  if (error) throw error
  
  return {
    user: {
      id: data.user!.id,
      email: data.user!.email!,
      name: name
    },
    session: data.session
  }
}

export const signInWithProvider = async (provider: 'google' | 'github') => {
  if (USE_DEV_AUTH) {
    // In dev-auth mode, simulate a provider sign-in by returning immediately
    return { provider, url: null }
  }
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${window.location.origin}/dashboard`
    }
  })
  
  if (error) throw error
  return data
}

export const signOut = async () => {
  if (USE_DEV_AUTH) return
  const { error } = await supabase.auth.signOut()
  if (error) throw error
}

export default api