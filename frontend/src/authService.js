/**
 * Authentication service for QueryVerse
 * Handles login, register, and token management
 */

import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/auth'

// Set up axios interceptor to handle 401 errors globally
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout and redirect to login
      authService.logout()
      window.location.hash = '#chat' // This will trigger the login page
    }
    return Promise.reject(error)
  }
)

// Store token in localStorage
const TOKEN_KEY = 'queryverse_token'
const USER_KEY = 'queryverse_user'

export const authService = {
  // Register a new user
  register: async (email, password, fullName) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/register`, {
        email,
        password,
        full_name: fullName
      })
      return response.data
    } catch (error) {
      throw error.response?.data || { detail: 'Registration failed' }
    }
  },

  // Login user
  login: async (email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/login`, {
        email,
        password
      })
      
      // Store token and user data
      localStorage.setItem(TOKEN_KEY, response.data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user))
      
      return response.data
    } catch (error) {
      throw error.response?.data || { detail: 'Login failed' }
    }
  },

  // Logout user
  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },

  // Get current token
  getToken: () => {
    return localStorage.getItem(TOKEN_KEY)
  },

  // Get current user
  getCurrentUser: () => {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem(TOKEN_KEY)
  },

  // Get auth headers for API calls
  getAuthHeaders: () => {
    const token = localStorage.getItem(TOKEN_KEY)
    return token ? { Authorization: `Bearer ${token}` } : {}
  },

  // Check if token is expired
  isTokenExpired: () => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) return true

    try {
      // JWT tokens have 3 parts separated by dots
      const parts = token.split('.')
      if (parts.length !== 3) return true

      // Decode the payload (second part)
      const payload = JSON.parse(atob(parts[1]))

      // Check if token has expiration time
      if (!payload.exp) return false

      // Check if current time is past expiration time (exp is in seconds)
      const currentTime = Math.floor(Date.now() / 1000)
      return payload.exp < currentTime
    } catch (error) {
      console.error('Error checking token expiration:', error)
      return true // Assume expired if we can't check
    }
  },

  // Validate session and redirect if expired
  validateSession: () => {
    if (authService.isTokenExpired()) {
      authService.logout()
      return false
    }
    return true
  }
}

export default authService
