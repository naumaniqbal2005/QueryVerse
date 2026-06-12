/**
 * Supabase Client Configuration
 * Handles Supabase client initialization for the frontend
 */

import { createClient } from '@supabase/supabase-js'

// Supabase configuration
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Validate environment variables
if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    'Missing Supabase environment variables. Please check your .env file.'
  )
}

// Create Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Export configuration for use in components
export const supabaseConfig = {
  url: supabaseUrl,
  anonKey: supabaseAnonKey
}

// Helper functions for common operations
export const supabaseHelpers = {
  // Auth helpers
  signUp: async (email, password) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password
    })
    return { data, error }
  },

  signIn: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    return { data, error }
  },

  signOut: async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  },

  getCurrentUser: async () => {
    const { data: { user }, error } = await supabase.auth.getUser()
    return { user, error }
  },

  // Database helpers
  fetch: async (table, options = {}) => {
    const { data, error } = await supabase
      .from(table)
      .select('*', options)
    return { data, error }
  },

  insert: async (table, data) => {
    const { data: result, error } = await supabase
      .from(table)
      .insert(data)
      .select()
    return { data: result, error }
  },

  update: async (table, data, filter) => {
    const { data: result, error } = await supabase
      .from(table)
      .update(data)
      .match(filter)
      .select()
    return { data: result, error }
  },

  delete: async (table, filter) => {
    const { error } = await supabase
      .from(table)
      .delete()
      .match(filter)
    return { error }
  }
}

export default supabase
