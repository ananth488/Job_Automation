'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  MessageSquare,
  X,
  Send,
  Bot,
  User,
  RotateCcw,
  Minimize2,
  Maximize2,
  Columns,
  ChevronDown,
  ArrowUpRight,
  Loader2,
  KeyRound,
  Check,
} from 'lucide-react';
import { toast } from 'sonner';
import { chatApi, type ChatMessagePayload } from '@/lib/api';

interface UIMessage {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: string;
}

export function AiChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  // Screen size: 'half' (50% screen - default), 'full' (fullscreen), 'compact' (floating card)
  const [sizeMode, setSizeMode] = useState<'half' | 'full' | 'compact'>('half');
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [geminiKey, setGeminiKey] = useState('');
  const [savedKey, setSavedKey] = useState('');

  const [messages, setMessages] = useState<UIMessage[]>([
    {
      id: 'welcome',
      role: 'model',
      content:
        'Hello! I am your **AI Career Copilot**.\n\nYou can ask me live questions about your **Jobs Discovered, Applications Tracker, Approval Queue, and Bot Status**, or ask any **Technical, Coding (React, Next.js, TypeScript), and Interview Preparation** questions!',
      timestamp: 'Just now',
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedKey = localStorage.getItem('gemini_api_key') || '';
      setGeminiKey(storedKey);
      setSavedKey(storedKey);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      inputRef.current?.focus();
    }
  }, [isOpen, messages, sizeMode]);

  const handleSaveKey = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== 'undefined') {
      const trimmed = geminiKey.trim();
      localStorage.setItem('gemini_api_key', trimmed);
      setSavedKey(trimmed);
      setShowKeyModal(false);
      toast.success(trimmed ? 'Gemini API Key saved!' : 'Gemini Key cleared. Using built-in engine.');
    }
  };

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    const userMsg: UIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const historyPayload: ChatMessagePayload[] = messages
        .filter((m) => m.id !== 'welcome')
        .slice(-6)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const res = await chatApi.sendMessage(text, historyPayload, savedKey);

      const botMsg: UIMessage = {
        id: `bot-${Date.now()}`,
        role: 'model',
        content: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch {
      toast.error('Could not get response from AI Copilot');
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'model',
          content: 'Sorry, I encountered an issue connecting to the AI server. Please try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: 'welcome-reset',
        role: 'model',
        content: 'Conversation cleared. How can I help you today?',
        timestamp: 'Just now',
      },
    ]);
  };

  // Cycle sizes: half -> full -> compact -> half
  const cycleSize = () => {
    if (sizeMode === 'half') setSizeMode('full');
    else if (sizeMode === 'full') setSizeMode('compact');
    else setSizeMode('half');
  };

  const getSizeClasses = () => {
    if (sizeMode === 'full') {
      return 'w-[calc(100vw-2rem)] h-[calc(100vh-2rem)] max-h-[96vh] right-4 bottom-4';
    }
    if (sizeMode === 'compact') {
      return 'w-[calc(100vw-2rem)] sm:w-[430px] h-[640px] max-h-[85vh] right-4 bottom-4';
    }
    // Default 'half' - 50% screen width, full height
    return 'w-full sm:w-[50vw] md:w-[48vw] min-w-[380px] max-w-[800px] h-[calc(100vh-2rem)] max-h-[96vh] right-4 bottom-4';
  };

  // Helper to render markdown links, bold text, and code blocks
  const renderFormattedMessage = (content: string) => {
    const parts = content.split(/(\[[^\]]+\]\([^)]+\))/g);

    return (
      <div className="space-y-1.5 leading-relaxed text-[13px]">
        {parts.map((part, index) => {
          const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
          if (linkMatch) {
            const [, label, url] = linkMatch;
            const isInternal = url.startsWith('/');
            if (isInternal) {
              return (
                <Link
                  key={index}
                  href={url}
                  onClick={() => setIsOpen(false)}
                  className="inline-flex items-center gap-1 font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-2 py-0.5 rounded transition-colors underline decoration-indigo-300"
                >
                  {label}
                  <ArrowUpRight className="w-3 h-3" />
                </Link>
              );
            }
            return (
              <a
                key={index}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 font-semibold text-indigo-600 hover:text-indigo-800 underline"
              >
                {label}
                <ArrowUpRight className="w-3 h-3" />
              </a>
            );
          }

          const lines = part.split('\n');
          return (
            <React.Fragment key={index}>
              {lines.map((line, lIdx) => {
                const isBullet = line.trim().startsWith('- ') || line.trim().startsWith('* ');
                const cleanLine = isBullet ? line.trim().substring(2) : line;
                const boldChunks = cleanLine.split(/(\*\*[^*]+\*\*)/g);

                return (
                  <p
                    key={lIdx}
                    className={`${isBullet ? 'flex items-start gap-1.5 pl-2' : ''} ${
                      cleanLine.startsWith('#') ? 'font-bold text-slate-900 mt-2 text-sm' : ''
                    }`}
                  >
                    {isBullet && <span className="text-indigo-500 font-bold">•</span>}
                    <span>
                      {boldChunks.map((chunk, cIdx) => {
                        if (chunk.startsWith('**') && chunk.endsWith('**')) {
                          return (
                            <strong key={cIdx} className="font-semibold text-slate-900">
                              {chunk.slice(2, -2)}
                            </strong>
                          );
                        }
                        return chunk;
                      })}
                    </span>
                  </p>
                );
              })}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  return (
    <>
      {/* Floating Trigger Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          title="Open AI Career Copilot"
          className="fixed bottom-6 right-6 z-50 group flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-600 text-white rounded-full shadow-xl shadow-indigo-600/30 hover:shadow-2xl hover:shadow-indigo-600/40 hover:scale-105 active:scale-95 transition-all duration-200 border border-indigo-400/30"
        >
          <div className="relative">
            <Sparkles className="w-5 h-5 text-indigo-200 animate-pulse" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-white" />
          </div>
          <span className="font-bold text-sm tracking-wide">AI Copilot</span>
          <span className="hidden sm:inline-block text-[11px] bg-white/20 px-2 py-0.5 rounded-full font-medium">
            Half Screen
          </span>
        </button>
      )}

      {/* Expandable Half-Screen / Full-Screen Chat Modal */}
      {isOpen && (
        <div
          className={`fixed z-50 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200 ${getSizeClasses()}`}
        >
          {/* Header */}
          <div className="px-4 py-3.5 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white flex items-center justify-between shadow-sm shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-inner">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-sm text-white leading-tight">AI Career Copilot</h3>
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-1.5 py-0.2 rounded-full">
                    <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-ping" />
                    Online
                  </span>
                  {sizeMode === 'half' && (
                    <span className="hidden sm:inline-block text-[9px] bg-indigo-500/30 text-indigo-200 px-1.5 py-0.5 rounded">
                      Half Screen
                    </span>
                  )}
                  {sizeMode === 'full' && (
                    <span className="hidden sm:inline-block text-[9px] bg-purple-500/30 text-purple-200 px-1.5 py-0.5 rounded">
                      Full Screen
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-300">Live Application Data & Universal Intelligence</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              {/* Configure Gemini API Key */}
              <button
                onClick={() => setShowKeyModal(!showKeyModal)}
                title="Configure Gemini API Key"
                className={`p-1.5 rounded-lg transition-colors ${
                  savedKey
                    ? 'text-emerald-400 hover:text-emerald-300 hover:bg-slate-700/50'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <KeyRound className="w-4 h-4" />
              </button>

              {/* Cycle Size (Half / Full / Compact) */}
              <button
                onClick={cycleSize}
                title={`Toggle Screen Size (Current: ${sizeMode})`}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
              >
                {sizeMode === 'half' ? (
                  <Maximize2 className="w-4 h-4" />
                ) : sizeMode === 'full' ? (
                  <Columns className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>

              {/* Clear chat */}
              <button
                onClick={handleClear}
                title="Clear Chat History"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              {/* Minimize/Close */}
              <button
                onClick={() => setIsOpen(false)}
                title="Close Chat"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
              >
                <Minimize2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Optional Gemini API Key Drawer */}
          {showKeyModal && (
            <div className="p-3 bg-slate-900 text-white border-b border-slate-700 text-xs shrink-0 animate-in fade-in duration-150">
              <form onSubmit={handleSaveKey} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">Google Gemini API Key (Optional):</span>
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] text-indigo-400 hover:underline"
                  >
                    Get Free Key &rarr;
                  </a>
                </div>
                <div className="flex gap-1.5">
                  <input
                    type="password"
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    placeholder="AIzaSy... (leave empty for built-in engine)"
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-hidden focus:border-indigo-500"
                  />
                  <button
                    type="submit"
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-xs"
                  >
                    Save
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/60">
            {messages.map((m) => {
              const isBot = m.role === 'model';
              return (
                <div
                  key={m.id}
                  className={`flex gap-2.5 ${isBot ? 'items-start' : 'items-start justify-end'}`}
                >
                  {isBot && (
                    <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5 shadow-sm">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-3.5 shadow-sm ${
                      isBot
                        ? 'bg-white border border-slate-200/80 text-slate-800'
                        : 'bg-indigo-600 text-white rounded-br-none'
                    }`}
                  >
                    {isBot ? (
                      renderFormattedMessage(m.content)
                    ) : (
                      <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{m.content}</p>
                    )}
                    <span
                      className={`block text-[10px] mt-1.5 ${
                        isBot ? 'text-slate-400' : 'text-indigo-200 text-right'
                      }`}
                    >
                      {m.timestamp}
                    </span>
                  </div>

                  {!isBot && (
                    <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center text-white shrink-0 mt-0.5">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="flex items-start gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl p-3 shadow-sm flex items-center gap-2 text-slate-500 text-xs">
                  <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
                  <span>Thinking & fetching response in English...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Footer */}
          <div className="p-3 sm:p-4 bg-white border-t border-slate-200 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="relative flex items-center bg-slate-100 hover:bg-slate-50 focus-within:bg-white border border-slate-200 focus-within:border-slate-400 focus-within:ring-2 focus-within:ring-slate-400/20 rounded-full transition-all px-4 py-1 shadow-inner"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything..."
                disabled={loading}
                className="flex-1 bg-transparent py-2 text-[13.5px] text-slate-800 focus:outline-hidden placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                title="Send message"
                className="p-2 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 disabled:opacity-50 text-white rounded-full transition-all shadow-sm shrink-0 ml-1.5"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
            <p className="text-[10.5px] text-center text-slate-400 mt-2">
              AI Copilot can make mistakes. Verify important application details.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
