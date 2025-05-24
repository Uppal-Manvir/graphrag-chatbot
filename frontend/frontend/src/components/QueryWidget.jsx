import React, { useState } from 'react';

export default function QueryWidget() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setAnswer(null);
    setSources([]);

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || 'Unknown error');
      }

      const data = await res.json();
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 max-w-xl mx-auto bg-white rounded-2xl shadow">
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          className="w-full p-2 border rounded"
          rows={4}
          placeholder="Ask me anything about Nestlé..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-2 bg-red-100 text-red-800 rounded">
          Error: {error}
        </div>
      )}

      {answer && (
        <div className="mt-4">
          <h2 className="text-xl font-semibold mb-2">Answer</h2>
          <p className="bg-gray-100 p-4 rounded">{answer}</p>
        </div>
      )}

      {sources.length > 0 && (
        <div className="mt-4">
          <h3 className="font-medium">Sources</h3>
          <ul className="list-disc list-inside">
            {sources.map((src, idx) => (
              <li key={idx} className="text-sm text-gray-600">
                {src}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
