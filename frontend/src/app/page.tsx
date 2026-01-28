'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Streamdown } from 'streamdown';
import remarkGfm from 'remark-gfm';
import {
  Forward,
  Wind,
  Zap,
  PanelsTopLeft,
  CirclePlus,
  Github,
  MessageSquare,
  History,
  Sun,
  Moon,
  Menu,
  X,
  Trash2
} from 'lucide-react';

interface Thread {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  message_count: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  responseTime?: number;
}

function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatStarted, setChatStarted] = useState(false);
  const [threadId, setThreadId] = useState<string>(generateUUID());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [isLoadingThreads, setIsLoadingThreads] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchThreads();
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    if (newMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }
  };

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const fetchThreads = async () => {
    setIsLoadingThreads(true);
    try {
      const response = await fetch('http://localhost:8000/threads');
      if (response.ok) {
        const data = await response.json();
        setThreads(data);
      }
    } catch (error) {
      console.error('Failed to fetch threads:', error);
    } finally {
      setIsLoadingThreads(false);
    }
  };

  const createThread = async (title?: string): Promise<string> => {
    try {
      const response = await fetch('http://localhost:8000/threads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      if (response.ok) {
        const thread = await response.json();
        setThreads(prev => [thread, ...prev]);
        return thread.id;
      }
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
    return generateUUID();
  };

  const loadThreadMessages = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/threads/${id}/messages`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
        setThreadId(id);
        setChatStarted(true);
      }
    } catch (error) {
      console.error('Failed to load thread messages:', error);
    }
  };

  const deleteThread = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this chat?')) return;

    try {
      const response = await fetch(`http://localhost:8000/threads/${id}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setThreads(prev => prev.filter(t => t.id !== id));
        // If we're currently viewing this thread, start a new chat
        if (threadId === id) {
          handleNewChat();
        }
      }
    } catch (error) {
      console.error('Failed to delete thread:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setChatStarted(true);
    setInput('');
    setIsLoading(true);

    const startTime = Date.now();

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input, thread_id: threadId }),
      });

      const finalResponseTime = Date.now() - startTime;

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let accumulated = '';

      let assistantMessageAdded = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulated += decoder.decode(value, { stream: true });

        if (!assistantMessageAdded && accumulated.trim()) {
          setMessages(prev => [...prev, { role: 'assistant', content: accumulated }]);
          assistantMessageAdded = true;
        } else if (assistantMessageAdded) {
          setMessages(prev => prev.map((msg, i) =>
            i === prev.length - 1 && msg.role === 'assistant'
              ? { ...msg, content: accumulated }
              : msg
          ));
        }
      }

      setMessages(prev => prev.map((msg, i) =>
        i === prev.length - 1 && msg.role === 'assistant'
          ? { ...msg, responseTime: finalResponseTime }
          : msg
      ));

      // Refresh threads list to show updated timestamp
      fetchThreads();
    } catch (error) {
      console.error('Error:', error);
      const responseTime = Date.now() - startTime;
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, there was an error processing your message.',
        responseTime: responseTime
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    // Delete all threads with 0 messages
    const emptyThreads = threads.filter(t => t.message_count === 0);
    
    for (const thread of emptyThreads) {
      try {
        await fetch(`http://localhost:8000/threads/${thread.id}`, {
          method: 'DELETE',
        });
      } catch (error) {
        console.error(`Failed to delete empty thread ${thread.id}:`, error);
      }
    }
    
    // Remove all empty threads from local state
    if (emptyThreads.length > 0) {
      const emptyThreadIds = new Set(emptyThreads.map(t => t.id));
      setThreads(prev => prev.filter(t => !emptyThreadIds.has(t.id)));
    }

    const newThreadId = await createThread();
    setMessages([]);
    setInput('');
    setIsLoading(false);
    setChatStarted(false);
    setThreadId(newThreadId);
  };


  const handleSelectThread = async (id: string) => {
    await loadThreadMessages(id);
  };

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
    if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  // Sidebar Component
  const Sidebar = () => (
    <aside
      className={`${sidebarOpen ? 'w-72 translate-x-0' : 'w-0 -translate-x-full'} transition-all duration-300 ease-in-out bg-[var(--surface-primary)] border-r border-[var(--border-primary)] flex flex-col overflow-hidden will-change-transform`}
    >
      <div className="p-4 border-b border-[var(--border-primary)]">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-background rounded-xl font-medium transition-all duration-200 shadow-[var(--shadow-sm)]"
        >
          <CirclePlus className="w-5 h-5" />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        <div className="px-4 mb-2 text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">
          Recent Chats
        </div>
        {isLoadingThreads ? (
          <div className="px-4 py-2 text-sm text-[var(--text-muted)]">Loading...</div>
        ) : threads.length === 0 ? (
          <div className="px-4 py-2 text-sm text-[var(--text-muted)]">No chats yet</div>
        ) : (
          <div className="space-y-1 px-2">
            {threads.map((thread) => (
              <div
                key={thread.id}
                onClick={() => handleSelectThread(thread.id)}
                className={`w-full flex items-center gap-3 px-3 py-3 text-left rounded-lg transition-all duration-200 group cursor-pointer ${threadId === thread.id
                  ? 'bg-[var(--surface-secondary)] text-[var(--text-primary)]'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--surface-secondary)] hover:text-[var(--text-primary)]'
                  }`}
              >
                <MessageSquare className={`w-4 h-4 ${threadId === thread.id ? 'text-[var(--accent-primary)]' : 'text-[var(--text-muted)] group-hover:text-[var(--accent-primary)]'} transition-colors`} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{thread.title}</div>
                  <div className="text-xs text-[var(--text-muted)]">{formatTime(thread.updated_at)}</div>
                </div>
                <button
                  onClick={(e) => deleteThread(thread.id, e)}
                  className="p-1 opacity-0 group-hover:opacity-100 transition-opacity text-[var(--text-muted)] hover:text-[var(--error)]"
                  title="Delete chat"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-[var(--border-primary)] space-y-2">
        <button
          onClick={fetchThreads}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)] rounded-lg transition-all duration-200"
        >
          <History className="w-4 h-4" />
          <span className="text-sm">Refresh</span>
        </button>
        <button
          onClick={toggleTheme}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)] rounded-lg transition-all duration-200"
        >
          {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          <span className="text-sm">{isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}</span>
        </button>
      </div>
    </aside>
  );

  // Welcome Screen
  if (!chatStarted) {
    return (
      <div className="h-screen flex bg-[var(--background)]">
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 flex flex-col relative overflow-hidden">
          {/* Top Bar */}
          <header className="flex items-center justify-between px-6 py-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)] rounded-lg transition-all duration-200"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            {/* Empty div for spacing */}
            <div></div>

            <button className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)] rounded-lg transition-all duration-200">
              <a href="https://github.com/federicodassie/arke" target="_blank" rel="noopener noreferrer">
                <Github className="w-5 h-5" />
              </a>
            </button>
          </header>

          {/* Welcome Content */}
          <div className="flex-1 flex flex-col items-center justify-center px-6 pb-20">
            <div className="text-center mb-12">
              <div className="flex items-center justify-center gap-4 mb-6">
                <img src="/arke-icon.png" className="w-22 h-22 unselectable" alt="Arke" />
                <h1 className="text-6xl font-bold text-[var(--text-primary)] logo-title unselectable">
                  Arke
                </h1>
              </div>
              <p className="text-lg text-[var(--text-secondary)] max-w-lg mx-auto">
                Your intelligent RAG assistant. Ask anything about your documents.
              </p>
            </div>

            {/* Input Area */}
            <div className="w-full max-w-2xl">
              <form onSubmit={handleSubmit} className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-neutral-400 to-neutral-600 rounded-2xl opacity-20 group-hover:opacity-40 transition duration-500 blur"></div>
                <div className="relative flex items-center bg-[var(--surface-primary)] rounded-2xl border border-[var(--border-primary)] shadow-[var(--shadow-sm)]">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Welcome! How can I assist you?"
                    className="flex-1 px-6 py-5 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none text-lg"
                    disabled={isLoading}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="mr-3 p-3 bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-background rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    <Forward className="w-5 h-5" />
                  </button>
                </div>
              </form>
            </div>

            {/* Feature Cards */}
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl w-full">
              <div className="group p-5 bg-[var(--surface-primary)] border border-[var(--border-primary)] rounded-xl hover:border-[var(--border-hover)] transition-all duration-300 shadow-[var(--shadow-sm)]">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-neutral-100 rounded-lg group-hover:bg-neutral-200 transition-colors">
                    <Wind className="w-5 h-5 text-neutral-600" />
                  </div>
                  <h3 className="font-semibold text-[var(--text-primary)]">What is Arke?</h3>
                </div>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Named after Arke, the swift messenger of the Titans. Now your assistant and your personal document manager.
                </p>
              </div>

              <div className="group p-5 bg-[var(--surface-primary)] border border-[var(--border-primary)] rounded-xl hover:border-[var(--border-hover)] transition-all duration-300 shadow-[var(--shadow-sm)]">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-neutral-100 rounded-lg group-hover:bg-neutral-200 transition-colors">
                    <Zap className="w-5 h-5 text-neutral-600" />
                  </div>
                  <h3 className="font-semibold text-[var(--text-primary)]">Key Efficiency</h3>
                </div>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Using modern frameworks, caching and optimizations to provide accurate, context-aware answers from your documents.
                </p>
              </div>

              <div className="group p-5 bg-[var(--surface-primary)] border border-[var(--border-primary)] rounded-xl hover:border-[var(--border-hover)] transition-all duration-300 shadow-[var(--shadow-sm)]">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-neutral-100 rounded-lg group-hover:bg-neutral-200 transition-colors">
                    <PanelsTopLeft className="w-5 h-5 text-neutral-600" />
                  </div>
                  <h3 className="font-semibold text-[var(--text-primary)]">Elegant Design</h3>
                </div>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  Clean, intuitive interface crafted for seamless user experience and visual harmony.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Chat Interface
  return (
    <div className="h-screen flex bg-[var(--background)]">
      <Sidebar />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Top Bar */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] bg-[var(--surface-primary)]">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)] rounded-lg transition-all duration-200"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <div className="flex items-center gap-2">
            <img src="/arke-icon.png" className="w-7 h-7 unselectable" alt="Arke" />
            <span className="text-lg font-bold text-[var(--text-primary)] logo-title unselectable">Arke</span>
          </div>

          <button className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)] rounded-lg transition-all duration-200">
            <a href="https://github.com/federicodassie/arke" target="_blank" rel="noopener noreferrer">
              <Github className="w-5 h-5" />
            </a>
          </button>
        </header>

        {/* Messages Area */}
        <div
          className="flex-1 overflow-y-auto px-4 py-6"
          ref={chatContainerRef}
        >
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 && (
              <div className="text-center text-[var(--text-muted)] py-10">
                Start the conversation by sending a message below.
              </div>
            )}
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div
                  className={`max-w-[100%] ${message.role === 'user'
                    ? 'bg-[var(--accent-primary)] text-background rounded-2xl rounded-tr-sm'
                    : 'bg-[var(--surface-primary)] border border-[var(--border-primary)] text-[var(--text-primary)]/80 rounded-2xl rounded-tl-sm'
                    } px-6 py-4 shadow-[var(--shadow-sm)]`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[var(--border-primary)]">
                      <img src="/arke-icon.png" className="w-5 h-5 rounded-full unselectable" alt="Arke" />
                      <span className="text-xs font-medium unselectable text-[var(--text-secondary)]">Arke Assistant</span>
                    </div>
                  )}

                  <div className="prose prose-sm max-w-none">
                    <Streamdown
                      className="prose prose-headings:font-[var(--font-montserrat-alternates)] max-w-none"
                      remarkPlugins={[remarkGfm]}
                    >
                      {message.content}
                    </Streamdown>
                  </div>

                  {message.responseTime && message.role === 'assistant' && (
                    <div className="mt-3 pt-2 border-t border-[var(--border-primary)] flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <Zap className="w-3 h-3" />
                      Response time: {(message.responseTime / 1000).toFixed(2)}s
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start animate-in fade-in duration-300">
                <div className="bg-[var(--surface-primary)] border border-[var(--border-primary)] rounded-2xl rounded-tl-sm px-6 py-4 shadow-[var(--shadow-sm)]">
                  <div className="flex items-center gap-3">
                    <img src="/arke-icon.png" className="w-5 h-5 rounded-full unselectable" alt="Arke" />
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-[var(--text-muted)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-[var(--text-secondary)]">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-[var(--border-primary)] bg-[var(--surface-primary)]">
          <div className="max-w-3xl mx-auto">
            <form onSubmit={handleSubmit} className="relative">
              <div className="relative flex items-center bg-[var(--surface-secondary)] rounded-2xl border border-[var(--border-primary)] focus-within:border-[var(--border-hover)] transition-colors">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything..."
                  className="flex-1 px-5 py-4 bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="mr-2 p-2.5 bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-background rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-[var(--shadow-sm)]"
                >
                  <Forward className="w-5 h-5" />
                </button>
              </div>
            </form>
            <div className="mt-2 text-center text-xs text-[var(--text-muted)]">
              Arke may produce inaccurate statements. Always verify important information.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
