import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

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
function ChatPage({ navHidden }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [isLoading, setIsLoading] = useState(false);
  const [tokensUsed, setTokensUsed] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Load chat state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('chatState');
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        setMessages(parsed.messages || []);
        setInput(parsed.input || '');
        setTemperature(parsed.temperature || 0.7);
        setTokensUsed(parsed.tokensUsed || null);
      } catch (e) {
        console.error('Failed to load chat state:', e);
      }
    }
  }, []);

  // Save chat state to localStorage whenever it changes
  useEffect(() => {
    const state = { messages, input, temperature, tokensUsed };
    localStorage.setItem('chatState', JSON.stringify(state));
  }, [messages, input, temperature, tokensUsed]);

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

    const userMessage = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);
    setTokensUsed(null);

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        message: input,
        chat_history: messages,
        temperature: temperature
      });

      const assistantMessage = { 
        role: 'assistant', 
        content: response.data.response 
      };
      
      setMessages([...newMessages, assistantMessage]);
      setTokensUsed(response.data.tokens_used);
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
    <div className="app">
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <div className="welcome-text">
            <h1>Say it, I'll fetch it</h1>
            <p>Ask me anything about your game rental database</p>
          </div>
          <div className="centered-input">
            <div className="input-row">
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
                className="send-button"
              >
                {isLoading ? 'Sending...' : 'Send'}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="chat-container">
          <div className="messages">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-avatar">
                  {message.role === 'user' ? 'U' : 'A'}
                </div>
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
                <div className="message-avatar">A</div>
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
      )}

      {messages.length > 0 && (
        <div className="input-container">
          <div className="input-row">
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
              className="send-button"
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      )}

      {/* Side Tabs */}
      <div className="side-tabs">
        <div className="side-tab creativity-tab">
          <div className="tab-header">
            <div className="tab-icon">
              <div className="icon-circle">C</div>
            </div>
            <span className="tab-text">Creativity</span>
          </div>
          <div className="tab-content">
            <div className="temperature-control">
              <label htmlFor="temperature">Response Creativity: {temperature.toFixed(1)}</label>
              <input
                id="temperature"
                type="range"
                min="0.2"
                max="1.0"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="temperature-slider"
              />
            </div>
          </div>
        </div>

        <div className="side-tab clear-tab">
          <div className="tab-header">
            <div className="tab-icon">
              <div className="icon-circle">X</div>
            </div>
            <span className="tab-text">Clear</span>
          </div>
          <div className="tab-content">
            <button onClick={clearChat} className="clear-button">
              Clear Chat
            </button>
          </div>
        </div>

        {tokensUsed && (
          <div className="side-tab tokens-tab">
            <div className="tab-header">
              <div className="tab-icon">
                <div className="icon-circle">T</div>
              </div>
              <span className="tab-text">Tokens</span>
            </div>
            <div className="tab-content">
              {formatTokens(tokensUsed)}
            </div>
          </div>
        )}
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

  // Create star particles for all pages
  useEffect(() => {
    const createStars = () => {
      const starsContainer = document.createElement('div');
      starsContainer.style.position = 'fixed';
      starsContainer.style.top = '0';
      starsContainer.style.left = '0';
      starsContainer.style.width = '100%';
      starsContainer.style.height = '100%';
      starsContainer.style.pointerEvents = 'none';
      starsContainer.style.zIndex = '4';
      document.body.appendChild(starsContainer);

      for (let i = 0; i < 40; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        
        const endX = (Math.random() - 0.5) * 2000;
        const endY = (Math.random() - 0.5) * 2000;
        star.style.setProperty('--end-x', `${endX}px`);
        star.style.setProperty('--end-y', `${endY}px`);
        
        star.style.animationDelay = `${Math.random() * 10}s`;
        star.style.animationDuration = `${10 + Math.random() * 10}s`;
        
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        
        const size = 1 + Math.random() * 2;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        
        star.style.opacity = 0.3 + Math.random() * 0.7;
        
        starsContainer.appendChild(star);
      }
    };

    createStars();
  }, []);

  return (
    <div className="app-wrapper">
      <button className="theme-toggle" onClick={toggleTheme}>
        {isInverted ? '☀️' : '🌙'}
      </button>
      {currentPage === '#home' && <HomePage navHidden={navHidden} />}
      {currentPage === '#chat' && <ChatPage navHidden={navHidden} />}
    </div>
  );
}

export default App;
