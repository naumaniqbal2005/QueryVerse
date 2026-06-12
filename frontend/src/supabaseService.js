/**
 * Supabase Service for QueryVerse
 * Handles all Supabase API calls for users, chats, databases, and messages
 */

import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/supabase'

// User operations
export const userService = {
  createUser: async (userData) => {
    const response = await axios.post(`${API_BASE_URL}/users`, userData)
    return response.data
  },

  getUser: async (userId) => {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}`)
    return response.data
  }
}

// Chat operations
export const chatService = {
  createChat: async (chatData, userId) => {
    const response = await axios.post(`${API_BASE_URL}/chats`, chatData, {
      params: { user_id: userId }
    })
    return response.data
  },

  getChat: async (chatId) => {
    const response = await axios.get(`${API_BASE_URL}/chats/${chatId}`)
    return response.data
  },

  listUserChats: async (userId) => {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/chats`)
    return response.data
  },

  updateChat: async (chatId, title) => {
    const response = await axios.put(`${API_BASE_URL}/chats/${chatId}`, null, {
      params: { title }
    })
    return response.data
  },

  deleteChat: async (chatId) => {
    const response = await axios.delete(`${API_BASE_URL}/chats/${chatId}`)
    return response.data
  }
}

// Database operations
export const databaseService = {
  uploadDatabase: async (file, userId, name) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post(`${API_BASE_URL}/databases/upload`, formData, {
      params: { user_id: userId, name },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  getDatabase: async (databaseId) => {
    const response = await axios.get(`${API_BASE_URL}/databases/${databaseId}`)
    return response.data
  },

  listUserDatabases: async (userId) => {
    const response = await axios.get(`${API_BASE_URL}/users/${userId}/databases`)
    return response.data
  },

  downloadDatabase: async (databaseId) => {
    const response = await axios.get(`${API_BASE_URL}/databases/${databaseId}/download`, {
      responseType: 'arraybuffer'
    })
    return {
      fileData: response.data.file_data,
      fileName: response.data.file_name,
      fileSize: response.data.file_size
    }
  },

  deleteDatabase: async (databaseId) => {
    const response = await axios.delete(`${API_BASE_URL}/databases/${databaseId}`)
    return response.data
  }
}

// Message operations
export const messageService = {
  createMessage: async (messageData, chatId) => {
    const response = await axios.post(`${API_BASE_URL}/messages`, messageData, {
      params: { chat_id: chatId }
    })
    return response.data
  },

  getChatMessages: async (chatId) => {
    const response = await axios.get(`${API_BASE_URL}/chats/${chatId}/messages`)
    return response.data
  },

  deleteMessage: async (messageId) => {
    const response = await axios.delete(`${API_BASE_URL}/messages/${messageId}`)
    return response.data
  }
}

// Chat-Database relationship operations
export const chatDatabaseService = {
  linkDatabaseToChat: async (chatId, databaseId) => {
    const response = await axios.post(`${API_BASE_URL}/chats/${chatId}/databases/${databaseId}`)
    return response.data
  },

  unlinkDatabaseFromChat: async (chatId, databaseId) => {
    const response = await axios.delete(`${API_BASE_URL}/chats/${chatId}/databases/${databaseId}`)
    return response.data
  },

  getChatDatabases: async (chatId) => {
    const response = await axios.get(`${API_BASE_URL}/chats/${chatId}/databases`)
    return response.data
  }
}

// Session operations
export const sessionService = {
  loadSession: async (chatId) => {
    const response = await axios.get(`${API_BASE_URL}/sessions/${chatId}`)
    return response.data
  },

  saveSession: async (chatId, messages, databaseIds) => {
    // Save all messages
    for (const message of messages) {
      await messageService.createMessage(
        {
          role: message.role,
          content: message.content,
          tokens_used: message.tokens_used
        },
        chatId
      )
    }

    // Link databases to chat
    for (const databaseId of databaseIds) {
      await chatDatabaseService.linkDatabaseToChat(chatId, databaseId)
    }

    return { success: true }
  }
}

export default {
  userService,
  chatService,
  databaseService,
  messageService,
  chatDatabaseService,
  sessionService
}
