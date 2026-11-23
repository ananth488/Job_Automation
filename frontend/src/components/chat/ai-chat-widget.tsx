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
  ChevronDown,
  ArrowUpRight,
  Loader2,
  CheckCircle2,
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
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<UIMessage[]>([
    {
      id: 'welcome',
      role: 'model',
      content:
        'வணக்கம்! நான் உங்களது **AI Career Copilot**.\n\nநமது Application-ல் உள்ள **Jobs, Applications, Approval Queue, Bot Status** பற்றிய நேரடி விபரங்கள் அல்லது எந்தவொரு **Coding / Technical / Interview** கேள்விகளையும் என்னிடம் கேட்கலாம்!',
      timestamp: 'Just now',
    },
  ]);
  const [suggestions, setSuggestions] = useState<string[]>([
    '📊 Innaki evlo jobs vanthuchu?',
    '⏳ Show jobs in my Approval Queue',
    '🎯 Next.js / React interview tips',
    '🤖 Is my Bot active and scheduled?',
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Fetch dynamic suggestions on mount
    chatApi
      .getSuggestions()
      .then((s) => {
        if (s && s.length > 0) setSuggestions(s);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      inputRef.current?.focus();
    }
  }, [isOpen, messages]);

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
      // Build history for context
      const historyPayload: ChatMessagePayload[] = messages
        .filter((m) => m.id !== 'welcome')
        .slice(-6)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const res = await chatApi.sendMessage(text, historyPayload);

      const botMsg: UIMessage = {
        id: `bot-${Date.now()}`,
        role: 'model',
        content: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      toast.error('Could not get response from AI Copilot');
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'model',
          content: 'மன்னிக்கவும், AI Server உடன் தொடர்புகொள்ள முடியவில்லை. தயவுசெய்து சிறிது நேரம் கழித்து மீண்டும் முயற்சிக்கவும்.',
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
        content: 'உரையாடல் ரீசெட் செய்யப்பட்டது. நீங்கள் என்ன தெரிந்து கொள்ள விரும்புகிறீர்கள்?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  // Helper to render markdown links, bold text, and linebreaks
  const renderFormattedMessage = (content: string) => {
    // Replace markdown links [Text](url)
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

          // Process bullet points and bold lines
          const lines = part.split('\n');
          return (
            <React.Fragment key={index}>
              {lines.map((line, lIdx) => {
                const isBullet = line.trim().startsWith('- ') || line.trim().startsWith('* ');
                const cleanLine = isBullet ? line.trim().substring(2) : line;

                // Process bold **text**
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
            Live DB
          </span>
        </button>
      )}

      {/* Expandable Chat Modal Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[calc(100vw-2rem)] sm:w-[430px] h-[600px] max-h-[85vh] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200">
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
                </div>
                <p className="text-[11px] text-slate-300">Live Application Data & Universal Intelligence</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={handleClear}
                title="Clear Chat History"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                title="Minimize Chat"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
              >
                <Minimize2 className="w-4 h-4" />
              </button>
            </div>
          </div>

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
                    className={`max-w-[85%] rounded-2xl p-3 shadow-sm ${
                      isBot
                        ? 'bg-white border border-slate-200/80 text-slate-800'
                        : 'bg-indigo-600 text-white rounded-br-none'
                    }`}
                  >
                    {isBot ? renderFormattedMessage(m.content) : <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{m.content}</p>}
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
                  <span>Thinking & fetching live state...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggestions Pill Carousel */}
          {suggestions.length > 0 && !loading && (
            <div className="px-3 py-2 bg-slate-100/90 border-t border-slate-200 flex items-center gap-1.5 overflow-x-auto no-scrollbar shrink-0">
              <span className="text-[11px] font-bold text-slate-500 shrink-0 px-1">Quick:</span>
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(s)}
                  className="whitespace-nowrap text-[11px] font-medium text-indigo-700 bg-white hover:bg-indigo-50 border border-indigo-200/70 hover:border-indigo-300 px-2.5 py-1 rounded-full transition-all shrink-0 shadow-xs"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input Footer */}
          <div className="p-3 bg-white border-t border-slate-200 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything about jobs, status, coding, interview..."
                disabled={loading}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                title="Send message"
                className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white rounded-xl transition-colors shadow-sm shrink-0"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
