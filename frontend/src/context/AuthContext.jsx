// Auth Context Provider
// =====================

import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../utils/supabase'

const AuthContext = createContext({})

export const useAuth = () => useContext(AuthContext)

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [session, setSession] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        // MOCK AUTH BYPASS: Force a demo user session
        const mockUser = {
            id: '00000000-0000-0000-0000-000000000000',
            email: 'demo@example.com',
            user_metadata: { full_name: 'Demo User' }
        }
        const mockSession = { user: mockUser, access_token: 'mock-token' }

        setUser(mockUser)
        setSession(mockSession)
        setLoading(false)

        // Listen for auth changes (keep as a no-op/fallback)
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (event, session) => {
                // Ignore real auth changes during bypass
                // setSession(session)
                // setUser(session?.user ?? null)
                // setLoading(false)
            }
        )

        return () => subscription.unsubscribe()
    }, [])

    const value = {
        user,
        session,
        loading,
        signUp: async (email, password) => {
            const { data, error } = await supabase.auth.signUp({ email, password })
            return { data, error }
        },
        signIn: async (email, password) => {
            const { data, error } = await supabase.auth.signInWithPassword({ email, password })
            return { data, error }
        },
        signInWithGoogle: async () => {
            const { data, error } = await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: `${window.location.origin}/dashboard`
                }
            })
            return { data, error }
        },
        signOut: async () => {
            const { error } = await supabase.auth.signOut()
            return { error }
        }
    }

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    )
}
