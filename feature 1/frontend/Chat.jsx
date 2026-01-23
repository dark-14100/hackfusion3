import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

export default function Chat() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  async function sendMessage(e) {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat/order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      setResponse(data);
    } catch (err) {
      console.error(err);
      setResponse({ error: "Request failed" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Pharmacy Chat</h2>
      <form onSubmit={sendMessage}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. I need 2 strips of paracetamol 500mg"
          style={{ width: "400px" }}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Processing..." : "Send"}
        </button>
      </form>

      {response && (
        <pre style={{ marginTop: "1rem", background: "#f5f5f5", padding: "1rem" }}>
          {JSON.stringify(response, null, 2)}
        </pre>
      )}
    </div>
  );
}