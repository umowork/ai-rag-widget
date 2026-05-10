(function() {
  const API_URL = window.AI_RAG_API_URL || "http://localhost:8000";
  const WIDGET_ID = "ai-rag-widget";

  // Styles
  const style = document.createElement("style");
  style.textContent = `
    #${WIDGET_ID} { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: sans-serif; }
    #${WIDGET_ID}-btn { width: 60px; height: 60px; border-radius: 50%; background: #2563eb; color: white; border: none; font-size: 24px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    #${WIDGET_ID}-chat { width: 350px; height: 500px; background: white; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15); display: none; flex-direction: column; overflow: hidden; border: 1px solid #e5e7eb; }
    #${WIDGET_ID}-header { background: #2563eb; color: white; padding: 16px; font-weight: 600; }
    #${WIDGET_ID}-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
    #${WIDGET_ID}-input { display: flex; border-top: 1px solid #e5e7eb; padding: 12px; gap: 8px; }
    #${WIDGET_ID}-input input { flex: 1; border: 1px solid #d1d5db; border-radius: 8px; padding: 8px 12px; outline: none; }
    #${WIDGET_ID}-input button { background: #2563eb; color: white; border: none; border-radius: 8px; padding: 8px 16px; cursor: pointer; }
    .rag-msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; }
    .rag-msg.user { background: #2563eb; color: white; align-self: flex-end; }
    .rag-msg.bot { background: #f3f4f6; color: #111; align-self: flex-start; }
    .rag-source { font-size: 11px; color: #6b7280; margin-top: 4px; }
  `;
  document.head.appendChild(style);

  // Container
  const container = document.createElement("div");
  container.id = WIDGET_ID;
  container.innerHTML = `
    <div id="${WIDGET_ID}-chat">
      <div id="${WIDGET_ID}-header">🤖 AI Assistant</div>
      <div id="${WIDGET_ID}-messages"></div>
      <div id="${WIDGET_ID}-input">
        <input type="text" placeholder="Введите вопрос..." />
        <button>→</button>
      </div>
    </div>
    <button id="${WIDGET_ID}-btn">💬</button>
  `;
  document.body.appendChild(container);

  // Elements
  const btn = document.getElementById(`${WIDGET_ID}-btn`);
  const chat = document.getElementById(`${WIDGET_ID}-chat`);
  const messages = document.getElementById(`${WIDGET_ID}-messages`);
  const input = chat.querySelector("input");
  const sendBtn = chat.querySelector("button");

  let isOpen = false;
  btn.onclick = () => {
    isOpen = !isOpen;
    chat.style.display = isOpen ? "flex" : "none";
  };

  function addMessage(text, isUser, sources) {
    const msg = document.createElement("div");
    msg.className = `rag-msg ${isUser ? "user" : "bot"}`;
    msg.textContent = text;
    messages.appendChild(msg);
    if (sources && sources.length) {
      const src = document.createElement("div");
      src.className = "rag-source";
      src.textContent = `Источники: ${sources.map(s => s.metadata?.source || "doc").join(", ")}`;
      messages.appendChild(src);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    addMessage(text, true);
    input.value = "";

    // Use streaming API
    const eventSource = new EventSource(`${API_URL}/chat/stream?query=${encodeURIComponent(text)}`);
    let botMsg = "";
    const msgDiv = document.createElement("div");
    msgDiv.className = "rag-msg bot";
    messages.appendChild(msgDiv);

    eventSource.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.token) {
        botMsg += data.token;
        msgDiv.textContent = botMsg;
        messages.scrollTop = messages.scrollHeight;
      }
      if (data.done) {
        eventSource.close();
        if (data.sources && data.sources.length) {
          const src = document.createElement("div");
          src.className = "rag-source";
          src.textContent = `Источники: ${data.sources.map(s => s.metadata?.source || "doc").join(", ")}`;
          messages.appendChild(src);
          messages.scrollTop = messages.scrollHeight;
        }
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      msgDiv.textContent = "Ошибка соединения. Попробуйте позже.";
    };
  }

  sendBtn.onclick = sendMessage;
  input.onkeypress = (e) => { if (e.key === "Enter") sendMessage(); };
})();
