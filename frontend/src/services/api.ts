/**
 * Client API backend avec intercepteurs axios
 */
import axios, { AxiosInstance, AxiosError } from 'axios'
import { getAccessToken } from './supabase'

const API_URL = import.meta.env.VITE_API_URL

if (!API_URL) {
  throw new Error('Missing VITE_API_URL environment variable')
}

/**
 * Instance axios configurée pour l'API backend
 */
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Intercepteur de requête : ajoute le token JWT
 */
api.interceptors.request.use(
  async (config) => {
    // Priorité au token localStorage (login via API backend)
    const localToken = localStorage.getItem('access_token')
    if (localToken) {
      config.headers.Authorization = `Bearer ${localToken}`
    } else {
      // Fallback: session Supabase
      const token = await getAccessToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Intercepteur de réponse : gestion des erreurs
 */
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data as Record<string, unknown>

      if (status === 401) {
        window.location.href = '/login'
      } else if (status === 403) {
        console.error('Accès interdit:', data.message)
      } else if (status === 404) {
        console.error('Ressource non trouvée:', data.message)
      } else if (status >= 500) {
        console.error('Erreur serveur:', data.message)
      }
    } else if (error.request) {
      console.error('Erreur réseau: Pas de réponse du serveur')
    }

    return Promise.reject(error)
  }
)

export default api

/**
 * Types de réponse API
 */
export interface ApiError {
  error: string
  message: string
  details?: Record<string, unknown>
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    per_page: number
    total: number
    total_pages: number
  }
}
