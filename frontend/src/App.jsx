import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import './Auth.css';
import { chatService, messageService, databaseService, chatDatabaseService, sessionService } from './supabaseService';
import authService from './authService';
import LoginPage from './LoginPage';
import { Upload, Send, Paperclip, Database, Plus, Settings, Trash2  } from 'lucide-react';

// Home Page Component
function HomePage({ navHidden }) {
  const [scrollClass, setScrollClass] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const greekTitleRef = useRef(null);
  const queryRef = useRef(null);
  const verseRef = useRef(null);
  const heroRef = useRef(null);
  const previousScrollClass = useRef('');

  // Helper functions to handle animation transitions properly
  const setScrollState = (el, className) => {
    // 1. Freeze the element at its current computed transform
    const current = getComputedStyle(el).transform;
    el.style.transform = current;        // inline style wins over animation
    el.style.animation = 'none';         // kill the keyframe immediately

    // 2. Force a reflow so the browser commits the frozen state
    void el.offsetHeight;

    // 3. Now swap to the scroll class — transition takes over cleanly
    el.classList.remove('scrolling', 'fade-out');
    el.classList.add(className);
    el.style.transform = '';             // let CSS classes drive it again
    el.style.animation = '';
  };

  const clearScrollState = (el) => {
    // 1. Freeze at current position
    const current = getComputedStyle(el).transform;
    el.style.transform = current;
    el.style.animation = 'none';
    void el.offsetHeight;

    // 2. Remove scroll classes — CSS transition takes it back to transform: none
    el.classList.remove('scrolling', 'fade-out');
    el.style.transform = '';   // let the base rule take over (no transform = identity)
    el.style.animation = 'none'; // keep animation suppressed during transition back

    // 3. After the transition finishes (0.6s), release animation suppression
    clearTimeout(el._floatTimer);
    el._floatTimer = setTimeout(() => {
      el.style.animation = '';  // now gentleFloat resumes from a clean resting state
    }, 650); // slightly longer than your 0.6s transition
  };

  // Main animation handler function
  const handleHeroAnimation = (newScrollClass, previousScrollClass) => {
    if (!heroRef.current) return;

    const hero = heroRef.current;
    
    if (newScrollClass === 'scrolling') {
      setScrollState(hero, 'scrolling');
    } else if (newScrollClass === 'fade-out') {
      setScrollState(hero, 'fade-out');
    } else if (previousScrollClass === 'scrolling' || previousScrollClass === 'fade-out') {
      // Scrolling up from scroll/fade-out state back to main
      clearScrollState(hero);
    }
  };

  // Measure query width for CSS positioning
  useEffect(() => {
    if (queryRef.current) {
      const w = queryRef.current.offsetWidth;
      document.documentElement.style.setProperty('--query-width', `${w + 20}px`);
    }
  }, []);

  useEffect(() => {
    // Loading buffer for smooth initialization
    const loadingTimer = setTimeout(() => {
      setIsLoading(false);
    }, 500); // Reduced from 1.5s to 0.5s

    const handleScroll = () => {
      if (isLoading) return; // Don't handle scroll during loading
      
      const scrollY = window.scrollY;
      let newScrollClass = '';
      
      if (scrollY > 300) {
        newScrollClass = 'fade-out';
      } else if (scrollY > 50) {
        newScrollClass = 'scrolling';
      } else {
        newScrollClass = '';
      }
      
      // Only apply FLIP animation when class actually changes
      if (newScrollClass !== previousScrollClass.current) {
        // Handle hero animation transitions with the new handler
        handleHeroAnimation(newScrollClass, previousScrollClass.current);
        
        previousScrollClass.current = newScrollClass;
      }
      
      setScrollClass(newScrollClass);
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(loadingTimer);
    };
  }, [isLoading]);

  return (
    <div className="brutalist-home">
      {/* Header Navigation */}
      <header className="brutalist-header">
        <div className="nav-left">DATABASE ASSISTANT</div>
        <div className="nav-center">
          {/* Empty for now */}
        </div>
        <div className="nav-right">
          <span onClick={() => window.location.hash = '#home'} style={{cursor: 'pointer'}}>HOME</span>
          <span>ABOUT</span>
          <span onClick={() => window.location.hash = '#chat'} style={{cursor: 'pointer'}}>CHAT</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="brutalist-main">
        {/* Interactive Hero Image */}
        <div className="hero-visual">
          <img 
            ref={heroRef}
            src="/images/phil.svg" 
            alt="Database Visualization" 
            className={`database-hero ${scrollClass} ${isLoading ? 'loading' : ''}`} 
          />
          
          {/* Greek-style Overlays */}
          <div className="greek-overlays">
            <div ref={greekTitleRef} className={`greek-title ${scrollClass}`}>
              <div ref={queryRef} className="greek-query">QUERY</div>
              <div ref={verseRef} className="greek-verse">VERSE</div>
            </div>
            <div className={`greek-subtitle ${scrollClass}`}>Ἡ ΠΥΞΙΑ ΤΗΣ ΓΝΩΣΗΣΣΗΣ</div>
          </div>
        </div>

        {/* Extended Content Cards */}
        <div className={`extended-content ${scrollClass}`}>
          <div className="content-grid">
            <div className="feature-card">
              <h3>Natural Language Queries</h3>
              <p>Ask questions in plain English, no SQL knowledge required</p>
            </div>
            <div className="feature-card">
              <h3>Real-time Processing</h3>
              <p>Get instant responses with optimized token usage</p>
            </div>
            <div className="feature-card">
              <h3>Accurate Results</h3>
              <p>Precise SQL generation and reliable data retrieval</p>
            </div>
          </div>
        </div>

        {/* Preview Card - Bottom Left */}
        <div className="preview-card">
          <div className="preview-overlay">QUERY INTERFACE</div>
        </div>

        {/* Sidebar - Right */}
        <div className="right-sidebar">
          <div className="sidebar-text">
            <div className="sidebar-initial">D.</div>
            <div className="sidebar-label">Database</div>
          </div>
        </div>

        {/* Footer - Bottom Right */}
        <div className="brutalist-footer">
          <div className="scroll-text">KEEP SCROLLING</div>
        </div>
      </main>
    </div>
  );
}

// Chat Component
function ChatPage({ navHidden, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [mode, setMode] = useState('query');
  const [isLoading, setIsLoading] = useState(false);
  const [tokensUsed, setTokensUsed] = useState(null);
  const [schemaInfo, setSchemaInfo] = useState(null);
  const [isUploadingSchema, setIsUploadingSchema] = useState(false);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [currentDatabaseId, setCurrentDatabaseId] = useState(null);
  const [userId, setUserId] = useState(null);
  const [chatList, setChatList] = useState([]);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [deletingChatId, setDeletingChatId] = useState(null);
  const [isRecentsExpanded, setIsRecentsExpanded] = useState(true);
  const [isTablesExpanded, setIsTablesExpanded] = useState(false);
  const [isModeExpanded, setIsModeExpanded] = useState(false);
  const [isCreativityExpanded, setIsCreativityExpanded] = useState(false);
  const [previousSql, setPreviousSql] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Initialize user ID from auth
  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (currentUser) {
      setUserId(currentUser.id);
      loadUserChats(currentUser.id);
    }
  }, []);

  // Load user's chats
  const loadUserChats = async (uid) => {
    try {
      const chats = await chatService.listUserChats(uid);
      setChatList(chats);
    } catch (error) {
      console.error('Failed to load chats:', error);
    }
  };

  // Load chat state from localStorage on mount (fallback for non-Supabase)
  useEffect(() => {
    if (!currentChatId) {
      const savedState = localStorage.getItem('chatState');
      if (savedState) {
        try {
          const parsed = JSON.parse(savedState);
          setMessages(parsed.messages || []);
          setInput(parsed.input || '');
          setTemperature(parsed.temperature || 0.7);
          setMode(parsed.mode || 'query');
          setTokensUsed(parsed.tokensUsed || null);
        } catch (e) {
          console.error('Failed to load chat state:', e);
        }
      }
    }
  }, [currentChatId]);

  // Save chat state to localStorage whenever it changes (fallback)
  useEffect(() => {
    if (!currentChatId) {
      const state = { messages, input, temperature, mode, tokensUsed };
      localStorage.setItem('chatState', JSON.stringify(state));
    }
  }, [messages, input, temperature, mode, tokensUsed, currentChatId]);

  // Create new chat
  const createNewChat = async () => {
    try {
      setCurrentChatId(null);
      setCurrentDatabaseId(null);
      setMessages([]);
      setTokensUsed(null);
      setSchemaInfo(null);
      setPreviousSql(null);
      setInput('');
      localStorage.removeItem('chatState');
    } catch (error) {
      console.error('Failed to start new chat:', error);
    }
  };

  const deleteChat = async (e, chatId) => {
    e.stopPropagation();
    if (!userId || deletingChatId) return;

    if (currentChatId === chatId && (isLoading || isLoadingChat)) {
      alert('Please wait for the current operation to finish before deleting this chat.');
      return;
    }

    const chat = chatList.find(c => c.id === chatId);
    const title = chat?.title || 'this chat';
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return;

    setDeletingChatId(chatId);
    try {
      await chatService.deleteChat(chatId, userId);
      setChatList(prev => prev.filter(c => c.id !== chatId));

      if (currentChatId === chatId) {
        setCurrentChatId(null);
        setCurrentDatabaseId(null);
        setMessages([]);
        setTokensUsed(null);
        setSchemaInfo(null);
        setInput('');
        setIsLoading(false);
        localStorage.removeItem('chatState');
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
      alert(`Failed to delete chat: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeletingChatId(null);
    }
  };

  // Load existing chat
  const loadChat = async (chatId) => {
    try {
      setIsLoadingChat(true);

      // Clear previous database state
      setCurrentDatabaseId(null);
      setSchemaInfo(null);
      setPreviousSql(null);
      
      const session = await sessionService.loadSession(chatId);
      
      // Parse messages from Supabase format
      const parsedMessages = session.messages.map(msg => ({
        role: msg.role === 'u' ? 'user' : 'assistant',
        content: msg.content,
        tokens_used: msg.tokens_used ? JSON.parse(msg.tokens_used) : null
      }));
      
      setMessages(parsedMessages);
      setCurrentChatId(chatId);
      
      // Load database files from storage and set up the database
      if (session.databases && session.databases.length > 0) {
        let databaseLoaded = false;
        
        for (const dbInfo of session.databases) {
          try {
            // Skip if fileData is null (download failed on backend)
            if (!dbInfo.fileData) {
              console.warn(`Database ${dbInfo.database.name} could not be downloaded: ${dbInfo.error || 'Unknown error'}`);
              continue;
            }
            
            // Create a Blob from the file data (SQL schema)
            const blob = new Blob([dbInfo.fileData], { type: 'application/sql' });
            const file = new File([blob], dbInfo.fileName, { type: 'application/sql' });
            
            // Upload to backend to set up the database
            const formData = new FormData();
            formData.append('file', file);
            
            const headers = authService.getAuthHeaders();
            const uploadResponse = await axios.post('http://localhost:8000/upload-schema', formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
                ...headers
              }
            });
            
            setSchemaInfo({
              status: uploadResponse.data.status,
              message: uploadResponse.data.message,
              schema: uploadResponse.data.db_schema,
              tables: uploadResponse.data.tables
            });
            
            setCurrentDatabaseId(dbInfo.database.id);
            databaseLoaded = true;
            console.log(`Database ${dbInfo.database.name} loaded successfully`);
            
            // Only load the first successfully downloaded database
            break;
          } catch (dbError) {
            console.error(`Failed to load database ${dbInfo.database.name}:`, dbError);
          }
        }
        
        if (!databaseLoaded) {
          console.warn('No database could be loaded for this chat');
          setSchemaInfo({
            status: 'warning',
            message: 'No database available for this chat. Please upload a database schema.',
            schema: null,
            tables: []
          });
        }
      } else {
        console.log('No databases linked to this chat');
        setSchemaInfo({
          status: 'info',
          message: 'No database linked to this chat. Please upload a database schema.',
          schema: null,
          tables: []
        });
      }
      
      // Refresh chat list to update active state
      await loadUserChats(userId);
      
      setIsLoadingChat(false);
    } catch (error) {
      console.error('Failed to load chat:', error);
      setIsLoadingChat(false);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [input]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // Create a chat if one doesn't exist
    let chatId = currentChatId;
    if (!chatId && userId) {
      try {
        const newChat = await chatService.createChat({ title: 'New Chat' }, userId);
        chatId = newChat.id;
        setCurrentChatId(chatId);
        await loadUserChats(userId);
      } catch (createError) {
        console.error('Failed to create chat:', createError);
      }
    }

    const userMessage = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);
    setTokensUsed(null);

    try {
      const headers = authService.getAuthHeaders();
      const response = await axios.post('http://localhost:8000/chat', {
        message: input,
        chat_history: messages,
        temperature: temperature,
        mode: mode,
        previous_sql: previousSql
      }, { headers });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        tokens_used: response.data.tokens_used
      };

      setMessages([...newMessages, assistantMessage]);
      setTokensUsed(response.data.tokens_used);

      // Update previous SQL if the response contains one
      if (response.data.sql_query) {
        setPreviousSql(response.data.sql_query);
      }

      // Auto-save to Supabase if chat exists
      if (chatId) {
        try {
          const savedUserMessage = await messageService.createMessage(
            {
              role: 'u',
              content: input,
              tokens_used: null
            },
            chatId
          );
          if (savedUserMessage.chat_title && userId) {
            await loadUserChats(userId);
          }
          await messageService.createMessage(
            {
              role: 'a',
              content: response.data.response,
              tokens_used: response.data.tokens_used
            },
            chatId
          );
        } catch (saveError) {
          console.error('Failed to save message to Supabase:', saveError);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { 
        role: 'assistant', 
        content: `❌ Error: ${error.response?.data?.detail || error.message}` 
      };
      setMessages([...newMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setTokensUsed(null);
    setPreviousSql(null);
    setInput('');
    if (!currentChatId) {
      localStorage.removeItem('chatState');
    }
  };

  const handleSchemaUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploadingSchema(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const headers = authService.getAuthHeaders();
      const response = await axios.post('http://localhost:8000/upload-schema', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...headers
        }
      });

      setSchemaInfo({
        status: response.data.status,
        message: response.data.message,
        schema: response.data.db_schema,
        tables: response.data.tables
      });

      // If database was stored in Supabase
      if (response.data.database_id) {
        setCurrentDatabaseId(response.data.database_id);
        
        // Create a chat if one doesn't exist, then link the database
        let chatId = currentChatId;
        if (!chatId && userId) {
          try {
            const newChat = await chatService.createChat({ title: 'New Chat' }, userId);
            chatId = newChat.id;
            setCurrentChatId(chatId);
            await loadUserChats(userId);
          } catch (createError) {
            console.error('Failed to create chat:', createError);
          }
        }
        
        // Link database to chat if we have a chat
        if (chatId) {
          try {
            await chatDatabaseService.linkDatabaseToChat(chatId, response.data.database_id);
            console.log('Database linked to chat successfully');
          } catch (linkError) {
            console.error('Failed to link database to chat:', linkError);
          }
        }
      }

      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error uploading schema:', error);
      alert(`Error uploading schema: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploadingSchema(false);
    }
  };

  const formatTokens = (tokens) => {
    if (!tokens) return null;
    return (
      <div className="token-info">
        <div className="token-total">
          <span className="token-label">Tokens Used:</span>
          <span className="token-value">{tokens.total}</span>
        </div>
        <div className="token-breakdown">
          <span className="token-input">Input: {tokens.input}</span>
          <span className="token-output">Output: {tokens.output}</span>
        </div>
        {tokens.sql_generation && (
          <div className="token-details">
            <small>
              <div>SQL Generation: {tokens.sql_generation.input} → {tokens.sql_generation.output}</div>
              <div>Response Generation: {tokens.response_generation.input} → {tokens.response_generation.output}</div>
            </small>
          </div>
        )}
      </div>
    );
  };

  const cleanResponse = (content) => {
    // Remove asterisks, clean up formatting
    return content
      .replace(/\*\*/g, '') // Remove bold asterisks
      .replace(/\*/g, '')   // Remove italic asterisks
      .replace(/❌/g, 'Error:')
      .replace(/⚠️/g, 'Warning:')
      .replace(/🔑/g, '')
      .replace(/⏳/g, '')
      .replace(/🔧/g, '')
      .replace(/⏱️/g, '')
      .replace(/🌐/g, '')
      .replace(/🎮/g, '')
      .replace(/SQL Query:/g, '')
      .replace(/Results:/g, '')
      .replace(/Tokens Used:/g, '')
      .replace(/\n\n+/g, '\n\n') // Clean up multiple newlines
      .trim();
  };

  return (
    <div className="chat-page">
      {/* Header Navigation */}
      <header className="brutalist-header">
        <div className="nav-left">DATABASE ASSISTANT</div>
        <div className="nav-center">
          {/* Empty for now */}
        </div>
        <div className="nav-right">
          <span onClick={() => window.location.hash = '#home'} style={{cursor: 'pointer'}}>HOME</span>
          <span>ABOUT</span>
          <span onClick={() => window.location.hash = '#chat'} style={{cursor: 'pointer'}}>CHAT</span>
        </div>
      </header>

      <div className="chat-layout">
      <aside className="chat-sidebar">
        <div className="sidebar-top">
          <button onClick={createNewChat} className="new-chat-button sidebar-new-chat">
            <Plus size={16} />
            <span>New Chat</span>
          </button>
        </div>

        <div className="sidebar-content">
          <div className="sidebar-expandable-section">
            <button onClick={() => setIsTablesExpanded(!isTablesExpanded)} className="new-chat-button sidebar-new-chat">
              <Database size={16} />
              <span>Table</span>
            </button>
            {isTablesExpanded && (
              <div className="sidebar-tables">
                {schemaInfo?.tables?.length > 0 ? (
                  <div className="tables-list-sidebar">
                    <div className="tables-header-sidebar">
                      <Database size={14} />
                      <span>Tables ({schemaInfo.tables.length})</span>
                    </div>
                    <div className="tables-list">
                      {schemaInfo.tables.map((table, index) => (
                        <div key={index} className="table-item">
                          <Database size={12} />
                          <span>{table}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="no-tables">No tables loaded</div>
                )}
              </div>
            )}
          </div>

          <div className="sidebar-expandable-section">
            <button onClick={() => setIsModeExpanded(!isModeExpanded)} className="new-chat-button sidebar-new-chat">
              <Settings size={16} />
              <span>Mode</span>
            </button>
            {isModeExpanded && (
              <div className="sidebar-mode-expanded">
                <button
                  type="button"
                  className={`sidebar-mode-option-expanded ${mode === 'query' ? 'active' : ''}`}
                  onClick={() => setMode('query')}
                >
                  <Database size={16} />
                  <div className="mode-option-content">
                    <span className="mode-option-title">Query</span>
                    <span className="mode-option-description">Generate SQL queries from natural language</span>
                  </div>
                </button>
                <button
                  type="button"
                  className={`sidebar-mode-option-expanded ${mode === 'general' ? 'active' : ''}`}
                  onClick={() => setMode('general')}
                >
                  <Send size={16} />
                  <div className="mode-option-content">
                    <span className="mode-option-title">General</span>
                    <span className="mode-option-description">General conversation and assistance</span>
                  </div>
                </button>
              </div>
            )}
          </div>

          <div className="sidebar-expandable-section">
            <button onClick={() => setIsCreativityExpanded(!isCreativityExpanded)} className="new-chat-button sidebar-new-chat">
              <Settings size={16} />
              <span>Creativity</span>
            </button>
            {isCreativityExpanded && (
              <div className="sidebar-creativity-expanded">
                <div className="creativity-content">
                  <div className="temp-header">
                    <label htmlFor="temperature-sidebar">{temperature.toFixed(1)}</label>
                  </div>
                  <div className="temp-description">AI Response Variability</div>
                  <input
                    id="temperature-sidebar"
                    type="range"
                    min="0.2"
                    max="1.0"
                    step="0.1"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="temperature-slider"
                  />
                  <div className="temp-labels">
                    <span className="temp-label">Precise</span>
                    <span className="temp-label">Creative</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="sidebar-recents">
            <div className="recents-header">
              <div className="recents-title">
                <span>Recents</span>
                <span className="recents-count">{chatList.length}</span>
              </div>
            </div>
            <div className="sidebar-chats expanded">
              {chatList.length === 0 ? (
                <div className="no-chats">No chats yet</div>
              ) : (
                chatList.map(chat => (
                  <div
                    key={chat.id}
                    className={`chat-list-item ${currentChatId === chat.id ? 'active' : ''} ${deletingChatId === chat.id ? 'deleting' : ''}`}
                    onClick={() => !deletingChatId && loadChat(chat.id)}
                  >
                    <div className="chat-item-content">
                      <div className="chat-item-title">{chat.title}</div>
                      <div className="chat-item-date">
                        {new Date(chat.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="chat-delete-button"
                      onClick={(e) => deleteChat(e, chat.id)}
                    disabled={deletingChatId === chat.id}
                    title="Delete chat"
                    aria-label={`Delete ${chat.title}`}
                  >
                    {deletingChatId === chat.id ? '…' : '×'}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-actions">
            <button onClick={onLogout} className="logout-button sidebar-logout-button">
              Logout
            </button>
          </div>
        </div>
      </aside>

      <main className="chat-main">
        {isLoadingChat ? (
          <div className="loading-screen">
            <div className="loading-content">
              <div className="loading-spinner"></div>
              <h2>Loading Chat...</h2>
              <p>Please wait while we load your previous conversation</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="welcome-screen">
            {!schemaInfo ? (
              <div className="upload-prompt">
                <div className="upload-icon-wrapper">
                  <Database className="upload-icon" size={64} />
                </div>
                <div className="upload-text">
                  <h2>No Database Loaded</h2>
                  <p>Upload your SQL schema to start querying your database</p>
                </div>
                <label htmlFor="welcome-schema-input" className="upload-prompt-button">
                  <Upload size={20} />
                  <span>Upload SQL Schema</span>
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".sql"
                  onChange={handleSchemaUpload}
                  disabled={isUploadingSchema}
                  className="schema-file-input"
                  id="welcome-schema-input"
                />
              </div>
            ) : (
              <>
                <div className="welcome-text">
                  <h1>Say it, I'll fetch it</h1>
                  <p>Ask me anything about your database</p>
                </div>
                <div className="centered-input">
                  <div className="input-wrapper">
                    <button
                      type="button"
                      className="input-icon attachment-icon"
                      onClick={() => fileInputRef.current?.click()}
                      title="Upload SQL Schema"
                    >
                      <Paperclip size={18} />
                    </button>
                    <button
                      type="button"
                      className="input-icon trash-icon"
                      onClick={clearChat}
                      title="Clear Messages"
                    >
                      <Trash2 size={18} />
                    </button>
                    <textarea
                      ref={textareaRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="What to bring you, my lord?"
                      className="message-input centered"
                      disabled={isLoading}
                      rows={1}
                    />
                    <button
                      onClick={sendMessage}
                      disabled={isLoading || !input.trim()}
                      className="input-icon send-icon"
                    >
                      {isLoading ? (
                        <span>Sending...</span>
                      ) : (
                        <Send size={18} />
                      )}
                    </button>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".sql"
                    onChange={handleSchemaUpload}
                    disabled={isUploadingSchema}
                    className="schema-file-input"
                    style={{ display: 'none' }}
                  />
                </div>
              </>
            )}
          </div>
        ) : (
          <>
            <div className="chat-container">
              <div className="messages">
                {messages.map((message, index) => (
                  <div key={index} className={`message ${message.role}`}>
                    <div className="message-content">
                      {message.role === 'assistant' ? (
                        cleanResponse(message.content).split('\n').map((line, lineIndex) => (
                          <div key={lineIndex}>
                            {line || <br />}
                          </div>
                        ))
                      ) : (
                        message.content.split('\n').map((line, lineIndex) => (
                          <div key={lineIndex}>
                            {line || <br />}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message assistant">
                    <div className="message-content loading">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <span className="loading-text">Thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            <div className="input-container">
              <div className="input-wrapper">
                <button
                  type="button"
                  className="input-icon attachment-icon"
                  onClick={() => fileInputRef.current?.click()}
                  title="Upload SQL Schema"
                >
                  <Paperclip size={18} />
                </button>
                <button
                  type="button"
                  className="input-icon trash-icon"
                  onClick={clearChat}
                  title="Clear Messages"
                >
                  <Trash2 size={18} />
                </button>
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="What to bring you, my lord?"
                  className="message-input"
                  disabled={isLoading}
                  rows={1}
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  className="input-icon send-icon"
                >
                  {isLoading ? (
                    <span>Sending...</span>
                  ) : (
                    <Send size={18} />
                  )}
                </button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".sql"
                onChange={handleSchemaUpload}
                disabled={isUploadingSchema}
                className="schema-file-input"
                style={{ display: 'none' }}
              />
            </div>
            <div className="input-black-box"></div>
          </>
        )}
      </main>
      </div>
    </div>
  );
}

// Main App Component with Navigation
function App() {
  const [currentPage, setCurrentPage] = useState(window.location.hash || '#home');
  const [chatState, setChatState] = useState({
    messages: [],
    input: '',
    temperature: 0.7,
    isLoading: false,
    tokensUsed: null
  });
  const [navHidden, setNavHidden] = useState(false);
  const [isInverted, setIsInverted] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentPage(window.location.hash || '#home');
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Toggle theme inversion
  const toggleTheme = () => {
    setIsInverted(!isInverted);
    document.body.classList.toggle('inverted');
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
    setCurrentPage('#home');
  };

  useEffect(() => {
    if (currentPage === '#home') {
      let lastScrollY = window.scrollY;
      const handleScroll = () => {
        const currentScrollY = window.scrollY;
        if (currentScrollY > lastScrollY && currentScrollY > 100) {
          setNavHidden(true);
        } else {
          setNavHidden(false);
        }
        lastScrollY = currentScrollY;
      };
      window.addEventListener('scroll', handleScroll);
      return () => window.removeEventListener('scroll', handleScroll);
    }
  }, [currentPage]);

  // Header hover detection for chat page
  useEffect(() => {
    if (currentPage === '#chat') {
      let hoverTimeout;
      const handleMouseMove = (e) => {
        clearTimeout(hoverTimeout);
        if (e.clientY <= 84) { // Header area
          setNavHidden(false);
        } else {
          hoverTimeout = setTimeout(() => {
            setNavHidden(true);
          }, 100);
        }
      };
      
      document.addEventListener('mousemove', handleMouseMove);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        clearTimeout(hoverTimeout);
      };
    }
  }, [currentPage]);

  // Load chat state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('chatState');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        setChatState(parsed);
      } catch (e) {
        console.error('Failed to load chat state:', e);
      }
    }
  }, []);

  // Save chat state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('chatState', JSON.stringify(chatState));
  }, [chatState]);

  const updateChatState = (updates) => {
    setChatState(prev => ({ ...prev, ...updates }));
  };

  return (
    <div className="app-wrapper">
      <button className="theme-toggle" onClick={toggleTheme}>
        {isInverted ? '☀️' : '🌙'}
      </button>
      {currentPage === '#home' && <HomePage navHidden={navHidden} />}
      {currentPage === '#chat' && (
        isAuthenticated ? (
          <ChatPage navHidden={navHidden} onLogout={handleLogout} />
        ) : (
          <LoginPage onLogin={handleLogin} />
        )
      )}
    </div>
  );
}

export default App;
