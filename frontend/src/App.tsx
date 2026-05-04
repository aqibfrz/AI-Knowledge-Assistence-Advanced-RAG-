import { FormEvent, useMemo, useState } from "react";

type Citation = {
  source: string;
  chunk_id: string;
  score: number;
  preview: string;
};

type Message = {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
};

const API_BASE = "http://localhost:8000";

function App() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [question, setQuestion] = useState("");
  const [url, setUrl] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [stats, setStats] = useState<{ total_documents: number; total_chunks: number; sessions: number } | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  const lastCitations = useMemo<Citation[]>(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i].citations?.length) return messages[i].citations ?? [];
    }
    return [];
  }, [messages]);

  const uploadFiles = async () => {
    if (!files?.length) return;
    const form = new FormData();
    Array.from(files).forEach((file) => form.append("files", file));
    setUploadStatus("Uploading files...");
    const response = await fetch(`${API_BASE}/ingest/files`, { method: "POST", body: form });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Upload failed" }));
      setUploadStatus(`Upload failed: ${errorData.detail ?? "Unknown error"}`);
      return;
    }
    setUploadStatus("Files uploaded successfully.");
    await fetchStats();
  };

  const uploadUrl = async () => {
    if (!url.trim()) return;
    setUploadStatus("Ingesting URL...");
    const response = await fetch(`${API_BASE}/ingest/url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "URL ingest failed" }));
      setUploadStatus(`URL ingest failed: ${errorData.detail ?? "Unknown error"}`);
      return;
    }
    setUploadStatus("URL ingested successfully.");
    setUrl("");
    await fetchStats();
  };

  const fetchStats = async () => {
    const res = await fetch(`${API_BASE}/admin/stats`);
    const data = await res.json();
    setStats(data);
  };

  const askQuestion = async (event: FormEvent) => {
    event.preventDefault();
    if (!question.trim() || isStreaming) return;
    const currentQuestion = question.trim();
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", text: currentQuestion }, { role: "assistant", text: "" }]);
    setIsStreaming(true);

    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question: currentQuestion }),
    });
    if (!response.body) {
      setIsStreaming(false);
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let citations: Citation[] = [];
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const eventText of events) {
        const lines = eventText.split("\n");
        const eventLine = lines.find((line) => line.startsWith("event: "));
        const dataLine = lines.find((line) => line.startsWith("data: "));
        if (!eventLine || !dataLine) continue;
        const eventType = eventLine.replace("event: ", "").trim();
        const data = dataLine.replace("data: ", "");
        if (eventType === "citations") {
          try {
            citations = JSON.parse(data);
          } catch {
            citations = [];
          }
        } else if (eventType === "token") {
          const token = data.replace(/\\n/g, "\n");
          setMessages((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            copy[copy.length - 1] = {
              role: "assistant",
              text: `${last.text}${token}`,
              citations,
            };
            return copy;
          });
        }
      }
    }
    setIsStreaming(false);
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>Knowledge Admin</h2>
        <div className="card">
          <label>Upload PDFs / DOCX</label>
          <input multiple type="file" accept=".pdf,.docx" onChange={(e) => setFiles(e.target.files)} />
          <button onClick={uploadFiles}>Ingest files</button>
          {uploadStatus ? <small>{uploadStatus}</small> : null}
        </div>
        <div className="card">
          <label>Ingest URL</label>
          <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/docs" />
          <button onClick={uploadUrl}>Ingest URL</button>
        </div>
        <div className="card">
          <button onClick={fetchStats}>Refresh Admin Stats</button>
          {stats && (
            <ul>
              <li>Documents: {stats.total_documents}</li>
              <li>Chunks: {stats.total_chunks}</li>
              <li>Sessions: {stats.sessions}</li>
            </ul>
          )}
        </div>
      </aside>
      <main className="chat">
        <h1>AI Knowledge Assistant</h1>
        <div className="messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <b>{message.role === "user" ? "You" : "Assistant"}:</b> {message.text}
            </div>
          ))}
        </div>
        <form onSubmit={askQuestion} className="ask-form">
          <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about your documents..." />
          <button type="submit" disabled={isStreaming}>
            {isStreaming ? "Thinking..." : "Send"}
          </button>
        </form>
        <section className="citations">
          <h3>Sources</h3>
          {lastCitations.length ? (
            lastCitations.map((citation) => (
              <article key={citation.chunk_id} className="citation">
                <div>
                  <b>{citation.source}</b> ({citation.chunk_id})
                </div>
                <small>{citation.preview}</small>
              </article>
            ))
          ) : (
            <p>No citations yet.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
