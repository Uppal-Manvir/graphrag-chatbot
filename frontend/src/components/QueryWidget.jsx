import React, { useState, useRef, useEffect } from 'react';

export default function QueryWidget() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (open) messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  const handleToggle = () => setOpen(prev => !prev);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userMsg = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    setQuestion('');
    setLoading(true);
    console.log("BEFORE TRY")

    try {
      console.log("BEFORE REQ")
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg.content })
      });
      console.log("SENT REQ")
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || 'Unknown error');
      }
      const { answer } = await res.json();
      const botMsg = { role: 'assistant', content: answer };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      const errorMsg = { role: 'assistant', content: '⚠️ ' + err.message };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Toggle button */}
      <button
        onClick={handleToggle}
        className="fixed bottom-4 right-4 z-50 p-3 bg-blue-600 rounded-full shadow-lg text-white hover:bg-blue-700 focus:outline-none"
      >
        {open ? 'Close' : 'AeroAdvisor'}
      </button>

      {/* Chat window */}
      {open && (
        <div className="fixed bottom-20 right-4 flex flex-col h-96 w-80 bg-white rounded-2xl shadow-lg overflow-hidden z-40">
            <div className="flex items-center justify-center p-2 bg-blue-600 text-white">
                <span className="font-semibold">AeroAdvisor</span>
            </div>
            <div className="flex-1 p-4 overflow-y-auto space-y-2">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={msg.role === 'user' ? 'text-right' : 'text-left'}
              >
                <span
                  className={
                    `inline-block px-3 py-2 rounded-2xl max-w-xs break-words ${
                      msg.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-900'
                    }`
                  }
                >
                  {msg.content}
                </span>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="flex p-2 space-x-2 border-t">
            <input
              type="text"
              className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Type your question…"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '...' : 'Send'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
