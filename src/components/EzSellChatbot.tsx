import { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { API_BASE_URL } from '@/lib/api';

// ── Types ──────────────────────────────────────────────────────────────────────
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: "Hey there! 👋 I'm your **EzSell Assistant** — ask me anything about posting ads, prices, AR viewing, or how our fraud system works. I'm here to help!",
};

const PAGE_LABEL_MAP: Record<string, string> = {
  '/': 'home',
  '/listings': 'listings',
  '/dashboard': 'dashboard',
  '/create-listing': 'create-listing',
  '/messages': 'messages',
  '/favorites': 'favorites',
  '/profile': 'profile',
};

function getPageLabel(pathname: string): string {
  if (pathname.startsWith('/product/')) return 'product';
  if (pathname.startsWith('/profile/')) return 'profile';
  return PAGE_LABEL_MAP[pathname] || 'home';
}

function getCategoryHint(pathname: string, messages: Message[]): string {
  const combined = messages.map(m => m.content).join(' ').toLowerCase();
  if (combined.includes('mobile') || combined.includes('phone') || combined.includes('iphone') || combined.includes('samsung')) return 'mobile';
  if (combined.includes('laptop') || combined.includes('macbook') || combined.includes('notebook')) return 'laptop';
  if (combined.includes('furniture') || combined.includes('sofa') || combined.includes('bed') || combined.includes('chair') || combined.includes('table')) return 'furniture';
  return '';
}

function extractKeywords(text: string): string[] {
  const stopWords = new Set(['the', 'a', 'an', 'is', 'are', 'for', 'of', 'in', 'to', 'how', 'much', 'what', 'price', 'cost', 'do', 'i', 'my', 'can', 'you']);
  return text.toLowerCase().split(/\s+/).filter(w => w.length > 2 && !stopWords.has(w)).slice(0, 5);
}

// ── Typing Indicator ───────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="ez-bot-bubble" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '12px 16px' }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: '50%',
          background: 'hsl(210 56% 60%)',
          display: 'inline-block',
          animation: `ezBotDot 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </div>
  );
}

// ── Message renderer with basic markdown ───────────────────────────────────────
function renderMarkdown(text: string) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n- /g, '<br/>• ')
    .replace(/\n(\d+)\. /g, '<br/>$1. ')
    .replace(/\n/g, '<br/>');
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function EzSellChatbot() {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([
    'How do I post an ad? 📋',
    'Check prices 💰',
    'AR viewing help 🪑',
  ]);
  const [hasUnread, setHasUnread] = useState(false);
  const [isFabHovered, setIsFabHovered] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const currentPage = getPageLabel(location.pathname);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Fetch suggestions for current page
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/chatbot/suggestions?page=${currentPage}`)
      .then(r => r.json())
      .then(d => { if (d.suggestions) setSuggestions(d.suggestions); })
      .catch(() => {});
  }, [currentPage]);

  // Flash unread badge when closed
  useEffect(() => {
    if (!isOpen && messages.length > 1) {
      const last = messages[messages.length - 1];
      if (last.role === 'assistant' && !last.streaming) setHasUnread(true);
    }
  }, [messages, isOpen]);

  const openChat = () => { setIsOpen(true); setHasUnread(false); inputRef.current?.focus(); };

  // ── Send message ──────────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text: string) => {
    const userText = text.trim();
    if (!userText || isStreaming) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: userText };
    const botMsgId = (Date.now() + 1).toString();
    const botMsg: Message = { id: botMsgId, role: 'assistant', content: '', streaming: true };

    setMessages(prev => [...prev, userMsg, botMsg]);
    setInput('');
    setIsStreaming(true);

    const historyForApi = [...messages, userMsg].slice(-10).map(m => ({
      role: m.role,
      content: m.content,
    }));

    const categoryHint = getCategoryHint(location.pathname, [...messages, userMsg]);
    const searchKeywords = extractKeywords(userText);

    try {
      abortRef.current = new AbortController();
      const res = await fetch(`${API_BASE_URL}/api/v1/chatbot/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: historyForApi,
          current_page: currentPage,
          category_hint: categoryHint,
          search_keywords: searchKeywords,
        }),
        signal: abortRef.current.signal,
      });

      if (!res.ok || !res.body) throw new Error('Network error');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.done) break;
            if (data.token) {
              setMessages(prev => prev.map(m =>
                m.id === botMsgId ? { ...m, content: m.content + data.token } : m
              ));
            }
          } catch {}
        }
      }
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        setMessages(prev => prev.map(m =>
          m.id === botMsgId ? { ...m, content: "Hmm, I couldn't connect. Please check your connection and try again! 🙏" } : m
        ));
      }
    } finally {
      setMessages(prev => prev.map(m =>
        m.id === botMsgId ? { ...m, streaming: false } : m
      ));
      setIsStreaming(false);
    }
  }, [messages, isStreaming, location.pathname, currentPage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); }
  };

  const clearChat = () => {
    abortRef.current?.abort();
    setMessages([WELCOME_MESSAGE]);
    setIsStreaming(false);
  };

  // ── Render ─────────────────────────────────────────────────────────────────────
  return (
    <>
      <style>{`
        @keyframes ezBotDot {
          0%,80%,100% { transform:scale(0.6); opacity:0.4; }
          40% { transform:scale(1); opacity:1; }
        }
        @keyframes ezFabGlow {
          0%,100% { box-shadow:0 0 0 0 hsl(210 56% 37%/0.5),0 6px 28px hsl(210 56% 37%/0.45); }
          50% { box-shadow:0 0 0 12px hsl(210 56% 37%/0),0 6px 28px hsl(210 56% 37%/0.7); }
        }
        @keyframes ezPanelIn {
          from { opacity:0; transform:translateY(20px) scale(0.96); }
          to { opacity:1; transform:translateY(0) scale(1); }
        }
        @keyframes ezMsgIn {
          from { opacity:0; transform:translateY(8px); }
          to { opacity:1; transform:translateY(0); }
        }
        @keyframes ezHeaderShimmer {
          0%,100% { background-position:0% 50%; }
          50% { background-position:100% 50%; }
        }
        @keyframes ezCursor {
          0%,100% { opacity:1; } 50% { opacity:0; }
        }
        .ez-bot-bubble {
          background:hsl(210 25% 13%);
          border:1px solid hsl(210 56% 37%/0.25);
          border-radius:4px 18px 18px 18px;
          padding:13px 17px;
          font-size:14.5px;
          line-height:1.7;
          color:hsl(210 20% 90%);
          animation:ezMsgIn 0.25s ease both;
          max-width:90%;
          word-break:break-word;
        }
        .ez-user-bubble {
          background:linear-gradient(135deg,hsl(210 56% 37%),hsl(212 47% 48%));
          border-radius:18px 4px 18px 18px;
          padding:13px 17px;
          font-size:14.5px;
          line-height:1.7;
          color:#fff;
          animation:ezMsgIn 0.25s ease both;
          max-width:90%;
          word-break:break-word;
          margin-left:auto;
        }
        .ez-chip {
          background:hsl(210 25% 16%);
          border:1px solid hsl(210 56% 37%/0.3);
          border-radius:20px;
          padding:7px 15px;
          font-size:13px;
          color:hsl(210 60% 75%);
          cursor:pointer;
          transition:all 0.2s;
          white-space:nowrap;
        }
        .ez-chip:hover {
          background:hsl(210 56% 37%/0.2);
          border-color:hsl(210 56% 37%/0.6);
          color:#fff;
          transform:translateY(-1px);
        }
        .ez-input {
          background:hsl(210 20% 11%);
          border:1px solid hsl(210 30% 22%);
          border-radius:14px;
          padding:12px 16px;
          font-size:14.5px;
          color:hsl(210 20% 90%);
          width:100%;
          resize:none;
          outline:none;
          font-family:inherit;
          transition:border-color 0.2s;
          line-height:1.55;
        }
        .ez-input:focus { border-color:hsl(210 56% 37%/0.7); }
        .ez-input::placeholder { color:hsl(210 15% 45%); }
        .ez-send-btn {
          width:44px; height:44px;
          background:linear-gradient(135deg,hsl(210 56% 37%),hsl(212 47% 48%));
          border:none; border-radius:12px; cursor:pointer;
          display:flex; align-items:center; justify-content:center;
          transition:all 0.2s; flex-shrink:0;
        }
        .ez-send-btn:hover:not(:disabled) { transform:scale(1.08); filter:brightness(1.1); }
        .ez-send-btn:disabled { opacity:0.45; cursor:not-allowed; }
        .ez-scrollbar::-webkit-scrollbar { width:4px; }
        .ez-scrollbar::-webkit-scrollbar-track { background:transparent; }
        .ez-scrollbar::-webkit-scrollbar-thumb { background:hsl(210 30% 25%); border-radius:4px; }
        .ez-cursor::after { content:'▋'; animation:ezCursor 0.9s infinite; font-size:11px; color:hsl(210 60% 65%); }
      `}</style>

      {/* ── Floating Action Button ─────────────────────────────────────────── */}
      <button
        id="ezsell-chatbot-fab"
          onClick={openChat}
          aria-label="Chat with AI Assistant"
          onMouseEnter={() => setIsFabHovered(true)}
          onMouseLeave={() => setIsFabHovered(false)}
          style={{
            position: 'fixed', bottom: 28, right: 28, zIndex: 9999,
            height: 68,
            width: isFabHovered ? 240 : 68,
            borderRadius: isFabHovered ? 34 : '50%',
            border: 'none',
            background: isFabHovered
              ? 'linear-gradient(135deg,hsl(210 56% 28%),hsl(212 47% 40%))'
              : 'linear-gradient(135deg,hsl(210 56% 32%),hsl(212 47% 44%))',
            cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            gap: isFabHovered ? 10 : 0,
            overflow: 'hidden',
            animation: isFabHovered ? 'none' : 'ezFabGlow 2.5s ease-in-out infinite',
            transition: 'width 0.35s cubic-bezier(0.34,1.56,0.64,1), border-radius 0.35s ease, background 0.2s ease, box-shadow 0.2s ease, transform 0.4s cubic-bezier(0.16,1,0.3,1), opacity 0.4s cubic-bezier(0.16,1,0.3,1), visibility 0.4s',
            boxShadow: isFabHovered
              ? '0 8px 32px hsl(210 56% 37%/0.55), 0 2px 8px hsl(210 56% 37%/0.3)'
              : undefined,
            paddingInline: isFabHovered ? 22 : 0,
            opacity: isOpen ? 0 : 1,
            visibility: isOpen ? 'hidden' : 'visible',
            transform: isOpen ? 'scale(0.8) translateY(20px)' : 'scale(1) translateY(0)',
            pointerEvents: isOpen ? 'none' : 'auto',
          }}
        >
          {/* Bot icon — scales up slightly on hover */}
          <svg
            width={isFabHovered ? 28 : 30}
            height={isFabHovered ? 28 : 30}
            viewBox="0 0 24 24" fill="none" stroke="white"
            strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
            style={{ flexShrink: 0, transition: 'all 0.3s ease' }}
          >
            <rect x="3" y="11" width="18" height="10" rx="2"/>
            <path d="M12 11V7"/>
            <circle cx="12" cy="5" r="2"/>
            <line x1="8" y1="15" x2="8" y2="17"/>
            <line x1="16" y1="15" x2="16" y2="17"/>
          </svg>

          {/* Label — fades in on hover */}
          <span style={{
            color: '#fff',
            fontSize: 14,
            fontWeight: 600,
            fontFamily: "'Plus Jakarta Sans','Inter',sans-serif",
            whiteSpace: 'nowrap',
            opacity: isFabHovered ? 1 : 0,
            maxWidth: isFabHovered ? 200 : 0,
            overflow: 'hidden',
            transform: isFabHovered ? 'translateX(0)' : 'translateX(-8px)',
            transition: 'opacity 0.25s ease 0.1s, transform 0.25s ease 0.1s, max-width 0.3s ease',
            letterSpacing: '0.01em',
          }}>
            Chat with AI Assistant
          </span>

          {/* Unread badge */}
          {hasUnread && (
            <span style={{
              position: 'absolute', top: 10, right: 10,
              width: 13, height: 13, borderRadius: '50%',
              background: '#ef4444',
              border: '2px solid hsl(210 56% 32%)',
              flexShrink: 0,
            }} />
          )}
        </button>

      {/* ── Chat Panel ────────────────────────────────────────────────────── */}
      <div
        id="ezsell-chatbot-panel"
          style={{
            position: 'fixed', bottom: 24, right: 24, zIndex: 9999,
            width: 'min(460px, calc(100vw - 24px))',
            height: 'min(640px, calc(100vh - 80px))',
            display: 'flex', flexDirection: 'column',
            background: 'hsl(210 25% 8%/0.97)',
            backdropFilter: 'blur(24px)',
            border: '1px solid hsl(210 56% 37%/0.3)',
            borderRadius: 22,
            boxShadow: '0 20px 60px hsl(210 56% 7%/0.7), 0 0 0 1px hsl(210 56% 37%/0.15)',
            transition: 'transform 0.4s cubic-bezier(0.16,1,0.3,1), opacity 0.4s cubic-bezier(0.16,1,0.3,1), visibility 0.4s',
            opacity: isOpen ? 1 : 0,
            visibility: isOpen ? 'visible' : 'hidden',
            transform: isOpen ? 'translateY(0) scale(1)' : 'translateY(20px) scale(0.96)',
            pointerEvents: isOpen ? 'auto' : 'none',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div style={{
            padding: '16px 18px',
            background: 'linear-gradient(135deg,hsl(210 56% 22%),hsl(212 47% 28%))',
            backgroundSize: '200% 200%',
            animation: 'ezHeaderShimmer 6s ease infinite',
            display: 'flex', alignItems: 'center', gap: 12,
            borderBottom: '1px solid hsl(210 56% 37%/0.2)',
            flexShrink: 0,
          }}>
            {/* Avatar */}
            <div style={{
              width: 42, height: 42, borderRadius: '50%',
              background: 'hsl(210 56% 37%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: '2px solid hsl(210 56% 60%/0.4)', flexShrink: 0,
            }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2"/>
                <path d="M12 11V7"/><circle cx="12" cy="5" r="2"/>
                <line x1="8" y1="15" x2="8" y2="17"/><line x1="16" y1="15" x2="16" y2="17"/>
              </svg>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ color: '#fff', fontWeight: 700, fontSize: 15.5, fontFamily: "'Plus Jakarta Sans',sans-serif" }}>
                EzSell Assistant
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginTop: 3 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', flexShrink: 0 }} />
                <span style={{ color: 'hsl(210 20% 72%)', fontSize: 12 }}>
                  {isStreaming ? 'Typing...' : 'Online'}
                </span>
              </div>
            </div>
            {/* Controls */}
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={clearChat} title="Clear chat" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'hsl(210 20% 65%)', padding: 4, borderRadius: 6, transition: 'color 0.2s' }}
                onMouseEnter={e => (e.currentTarget.style.color = '#fff')} onMouseLeave={e => (e.currentTarget.style.color = 'hsl(210 20% 65%)')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.51"/>
                </svg>
              </button>
              <button onClick={() => setIsOpen(false)} title="Minimize" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'hsl(210 20% 65%)', padding: 4, borderRadius: 6, transition: 'color 0.2s' }}
                onMouseEnter={e => (e.currentTarget.style.color = '#fff')} onMouseLeave={e => (e.currentTarget.style.color = 'hsl(210 20% 65%)')}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="ez-scrollbar" style={{ flex: 1, overflowY: 'auto', padding: '18px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {messages.map((msg, idx) => (
              <div key={msg.id} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                {msg.role === 'assistant' ? (
                  <div className={`ez-bot-bubble${msg.streaming && msg.content ? ' ez-cursor' : ''}`}
                    dangerouslySetInnerHTML={{ __html: msg.content ? renderMarkdown(msg.content) : '' }}
                  />
                ) : (
                  <div className="ez-user-bubble">{msg.content}</div>
                )}
                {/* Timestamp on last message */}
                {idx === messages.length - 1 && (
                  <span style={{ fontSize: 11, color: 'hsl(210 15% 42%)', marginTop: 4, paddingInline: 4 }}>
                    {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>
            ))}
            {/* Typing indicator when awaiting first token */}
            {isStreaming && messages[messages.length - 1]?.content === '' && (
              <div style={{ display: 'flex', alignItems: 'flex-start' }}>
                <TypingDots />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick suggestion chips */}
          {!isStreaming && (
            <div style={{ padding: '0 16px 12px', display: 'flex', gap: 7, flexWrap: 'wrap', flexShrink: 0 }}>
              {suggestions.map(s => (
                <button key={s} className="ez-chip" onClick={() => sendMessage(s)}>{s}</button>
              ))}
            </div>
          )}

          {/* Input bar */}
          <div style={{
            padding: '12px 16px 16px',
            borderTop: '1px solid hsl(210 25% 15%)',
            background: 'hsl(210 25% 7%)',
            display: 'flex', gap: 10, alignItems: 'flex-end', flexShrink: 0,
          }}>
            <textarea
              ref={inputRef}
              id="ezsell-chatbot-input"
              className="ez-input"
              rows={1}
              value={input}
              onChange={e => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything…"
              disabled={isStreaming}
              style={{ maxHeight: 120 }}
            />
            <button
              id="ezsell-chatbot-send"
              className="ez-send-btn"
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isStreaming}
              aria-label="Send message"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
    </>
  );
}
