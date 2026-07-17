// API Service Client
// ===================

import axios from 'axios'
import { supabase } from './supabase'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance with auth interceptor
const api = axios.create({
    baseURL: `${API_URL}/api`,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Add auth token to all requests
api.interceptors.request.use(async (config) => {
    const { data: { session } } = await supabase.auth.getSession()

    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`
    }

    return config
})

// Handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Redirect to login on auth error
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default api

// ============================================================================
// Stock API
// ============================================================================

export const stockApi = {
    getData: (ticker) => api.get(`/stock/${ticker}`),
    getInfo: (ticker) => api.get(`/stock/${ticker}/info`),
    getMarketIndices: () => api.get('/stock/market/indices'),
    getHistory: (ticker, period = '1mo') => api.get(`/stock/${ticker}/history?period=${period}`),
    getNews: (ticker, limit = 10) => api.get(`/stock/${ticker}/news?limit=${limit}`),
    getVideos: (ticker, limit = 4) => api.get(`/stock/${ticker}/videos?limit=${limit}`),
    getMarketNews: (limit = 20) => api.get(`/stock/market/news?limit=${limit}`),
    getSentimentHistory: (ticker, days = 30) => api.get(`/stock/${ticker}/sentiment-history?days=${days}`),
    getSocialSentiment: (ticker) => api.get(`/stock/${ticker}/social-sentiment`),
    getStockTwitsSentiment: (ticker) => api.get(`/stock/${ticker}/stocktwits`),
    getTwitterSentiment: (ticker) => api.get(`/stock/${ticker}/twitter-sentiment`),
}

// ============================================================================
// Analysis API
// ============================================================================

export const analysisApi = {
    start: (data) => api.post('/analysis/start', data),
    getResult: (jobId) => api.get(`/analysis/${jobId}`),
    sentiment: (data) => api.post('/analysis/sentiment', data),
    forecast: (data) => api.post('/analysis/forecast', data),
    recommend: (data) => api.post('/analysis/recommend', data),
    fhi: (data) => api.post('/analysis/fhi', data),
    getSchedules: () => api.get('/analysis/schedules'),
    createSchedule: (data) => api.post('/analysis/schedule', data),
    deleteSchedule: (jobId) => api.delete(`/analysis/schedule/${jobId}`),
}

// ============================================================================
// Documents API
// ============================================================================

export const documentsApi = {
    upload: (file, docType = 'general') => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('doc_type', docType)
        return api.post('/documents/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        })
    },
    list: () => api.get('/documents'),
    delete: (docId) => api.delete(`/documents/${docId}`),
    search: (query, topK = 5) => api.post('/documents/search', { query, top_k: topK }),
}

// ============================================================================
// Chat API
// ============================================================================

export const chatApi = {
    query: (message, ticker = null, document_ids = []) => api.post('/chat/query', { message, ticker, document_ids }),
    getHistory: (limit = 50) => api.get(`/chat/history?limit=${limit}`),
    clearHistory: () => api.delete('/chat/history'),
}

// ============================================================================
// Reports API
// ============================================================================

export const reportsApi = {
    list: () => api.get('/reports'),
    download: (reportId) => api.get(`/reports/${reportId}/download`, { responseType: 'blob' }),
    getData: (reportId) => api.get(`/reports/${reportId}/data`),
    delete: (reportId) => api.delete(`/reports/${reportId}`),
    generate: (data) => api.post('/reports/generate', data),
    emailReport: (reportId, email) => api.post(`/reports/${reportId}/email`, { report_id: reportId, email }),
}
