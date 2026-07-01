import { useRef, useState } from 'react';
import { sendChat } from '../api';

const STARTERS = [
  'Should I cut the onion rings? Nobody orders them.',
  'What combos should we promote?',
  'Which items are Stars vs Dogs?',
];

export default function ChatPanel({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  async function handleSend(question) {
    const text = (question ?? input).trim();
    if (!text || loading) return;

    setInput('');
    setError(null);
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setLoading(true);

    try {
      const response = await sendChat(text, sessionId);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.answer, data: response.structured_data },
      ]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  }

  return (
    <div className="card chat-card">
      <div className="card-header chat-header">
        <div>
          <h2>Ask MenuIQ</h2>
          <p className="muted">Agent selects analytics tools to answer your question</p>
        </div>
        <span className="chat-status">AI</span>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p className="chat-empty-title">Starter questions</p>
            <div className="starter-row">
              {STARTERS.map((q) => (
                <button key={q} type="button" className="starter-btn" onClick={() => handleSend(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble chat-${msg.role}`}>
            <span className="chat-role">{msg.role === 'user' ? 'You' : 'MenuIQ'}</span>
            <p>{msg.content}</p>
            {msg.data?.items && (
              <div className="tag-row">
                {msg.data.items.map((item) => (
                  <span key={item} className="item-tag">{item}</span>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-bubble chat-assistant">
            <span className="chat-role">MenuIQ</span>
            <p className="typing">Analyzing menu data…</p>
          </div>
        )}
        {error && <div className="error-banner">{error}</div>}
        <div ref={bottomRef} />
      </div>

      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about items, pairings, or cuts…"
          disabled={loading}
        />
        <button type="submit" className="btn-primary" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
