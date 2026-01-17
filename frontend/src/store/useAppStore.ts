import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User, Session } from '@supabase/supabase-js'

interface AppUser {
  id: string
  email: string
  name: string
}

interface PatientCase {
  patientId: string
  age: number
  gender: string
  symptoms: string
  medicalHistory: string
  currentMedications: string | string[] // Allow both string and array
  urgency: 'low' | 'medium' | 'high' | 'critical'
}

interface AgentResult {
  agentName: string
  status: 'pending' | 'running' | 'completed' | 'error'
  result?: any
  timestamp?: Date
}

interface AppState {
  // Auth state
  user: AppUser | null
  session: Session | null
  isAuthenticated: boolean
  setAuth: (user: AppUser | null, session: Session | null) => void
  clearAuth: () => void
  
  // Dashboard state
  stats: {
    activeAgents: number
    completedCases: number
    casesAnalyzed: number
    progress: number
    totalAnalysisTime: number // in seconds
  }
  updateStats: (updates: Partial<AppState['stats']>) => void
  incrementCompletedCases: () => void
  incrementCasesAnalyzed: () => void
  
  // Case state
  currentCase: PatientCase | null
  setCurrentCase: (patientCase: PatientCase) => void
  
  // Analysis state
  agentResults: AgentResult[]
  analysisInProgress: boolean
  setAnalysisInProgress: (inProgress: boolean) => void
  updateAgentResult: (agentName: string, status: AgentResult['status'], result?: any) => void
  clearResults: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Auth state
      user: null,
      session: null,
      isAuthenticated: false,
      setAuth: (user, session) => set({ user, session, isAuthenticated: !!user }),
      clearAuth: () => set({ user: null, session: null, isAuthenticated: false }),
      
      // Dashboard state
      stats: {
        activeAgents: 5,  // Total AI agents in system
        completedCases: 0,  // Successfully completed analyses
        casesAnalyzed: 0,  // Total analyses run
        progress: 0,  // Current analysis progress %
        totalAnalysisTime: 0  // Total time spent on analyses (seconds)
      },
      updateStats: (updates) => set((state) => ({
        stats: { ...state.stats, ...updates }
      })),
      incrementCompletedCases: () => set((state) => ({
        stats: { ...state.stats, completedCases: state.stats.completedCases + 1 }
      })),
      incrementCasesAnalyzed: () => set((state) => ({
        stats: { ...state.stats, casesAnalyzed: state.stats.casesAnalyzed + 1 }
      })),
      
      // Case state
      currentCase: null,
      setCurrentCase: (currentCase) => set({ currentCase }),
      
      // Analysis state
      agentResults: [],
      analysisInProgress: false,
      setAnalysisInProgress: (analysisInProgress) => set({ analysisInProgress }),
      updateAgentResult: (agentName, status, result) => set((state) => {
        const existingIndex = state.agentResults.findIndex(ar => ar.agentName === agentName)
        const newResult: AgentResult = {
          agentName,
          status,
          result,
          timestamp: new Date()
        }
        
        if (existingIndex >= 0) {
          const newResults = [...state.agentResults]
          newResults[existingIndex] = newResult
          return { agentResults: newResults }
        } else {
          return { agentResults: [...state.agentResults, newResult] }
        }
      }),
      clearResults: () => set({ agentResults: [] })
    }),
    {
      name: 'medsai-storage', // localStorage key
      partialize: (state) => ({ 
        stats: state.stats // Only persist stats, not auth or analysis state
      })
    }
  )
)