const STORAGE_KEY = "veronica.v4.conversation";
const WELCOME = "Veronica’s interface is ready. Connect the text model to begin. No model-generated response has been produced yet.";

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

function formatInline(raw) {
  const codes = [];
  let text = String(raw).replace(/`([^`]+)`/g, (_, code) => {
    codes.push(`<code>${escapeHtml(code)}</code>`);
    return `\u0000CODE${codes.length - 1}\u0000`;
  });
  text = escapeHtml(text)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s<)]+)\)/g, '<a href="$2" rel="noopener noreferrer" target="_blank">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(^|[^\w*])\*([^*]+)\*/g, "$1<em>$2</em>");
  return text.replace(/\u0000CODE(\d+)\u0000/g, (_, index) => codes[Number(index)]);
}

function markdownToSafeHtml(text) {
  const source = String(text ?? "");
  const fences = [];
  const prepared = source.replace(/```([a-zA-Z0-9_+-]*)[ \t]*\r?\n?([\s\S]*?)```/g, (_, lang, code) => {
    const cls = lang ? ` class="language-${escapeHtml(lang)}"` : "";
    fences.push(`<pre><code${cls}>${escapeHtml(code.replace(/\n$/, ""))}</code></pre>`);
    return `\n\n\u0000FENCE${fences.length - 1}\u0000\n\n`;
  });
  const html = prepared.split(/\n{2,}/).map((block) => {
    const trimmed = block.trim();
    if (!trimmed) return "";
    const fence = /^\u0000FENCE(\d+)\u0000$/.exec(trimmed);
    if (fence) return fences[Number(fence[1])];
    const lines = trimmed.split(/\n/);
    const heading = /^(#{1,3}) (.+)$/.exec(trimmed);
    if (heading && lines.length === 1) return `<h${heading[1].length}>${formatInline(heading[2])}</h${heading[1].length}>`;
    if (lines.every((line) => /^[-*] /.test(line))) {
      return `<ul>${lines.map((line) => `<li>${formatInline(line.slice(2))}</li>`).join("")}</ul>`;
    }
    if (lines.every((line) => /^\d+\. /.test(line))) {
      return `<ol>${lines.map((line) => `<li>${formatInline(line.replace(/^\d+\. /, ""))}</li>`).join("")}</ol>`;
    }
    if (lines.every((line) => /^> /.test(line))) {
      return `<blockquote>${lines.map((line) => formatInline(line.slice(2))).join("<br>")}</blockquote>`;
    }
    return `<p>${formatInline(trimmed).replace(/\n/g, "<br>")}</p>`;
  }).join("");
  return html;
}

function serializeConversation(messages, mode) {
  const stored = messages.map((item) => {
    const row = { role: item.role, content: item.content };
    if (item.status && item.status !== "streaming") row.status = item.status;
    if (item.status === "streaming") {
      row.status = item.content ? "stopped" : "error";
      if (!item.content) row.error = "Interrupted";
    } else if (item.error) row.error = item.error;
    return row;
  }).filter((item) => item.role === "user" || item.role === "assistant");
  return JSON.stringify({ version: 1, messages: stored, mode });
}

function deserializeConversation(raw) {
  if (!raw) return null;
  try {
    const data = JSON.parse(raw);
    if (!data || !Array.isArray(data.messages)) return null;
    const messages = data.messages.filter((item) => (
      item && (item.role === "user" || item.role === "assistant") && typeof item.content === "string"
    )).map((item) => {
      const row = { role: item.role, content: item.content };
      if (item.status === "error" || item.status === "stopped" || item.status === "complete") row.status = item.status;
      if (typeof item.error === "string") row.error = item.error;
      if (row.status === "streaming") row.status = row.content ? "stopped" : "error";
      return row;
    });
    const mode = typeof data.mode === "string" ? data.mode : "chat";
    return { messages, mode };
  } catch {
    return null;
  }
}

function bootChat() {
  const conversation = document.querySelector("#conversation");
  const composer = document.querySelector("#composer");
  const promptInput = document.querySelector("#prompt");
  const modeInput = document.querySelector("#mode");
  const sendButton = document.querySelector("#sendChat");
  const stopButton = document.querySelector("#stopChat");
  const notice = document.querySelector("#notice");
  const runtimeStatus = document.querySelector("#runtimeStatus");
  const providerSummary = document.querySelector("#providerSummary");
  const providerState = document.querySelector("#providerState");
  const backendPill = document.querySelector("#chatBackendPill");
  const corePanel = document.querySelector(".current-task-panel");
  const coreState = document.querySelector("#coreState");
  const coreDetail = document.querySelector("#coreDetail");
  const activityList = document.querySelector("#activityList");
  const messages = [];
  let pending = false;
  let abortController = null;
  let generation = 0;
  let streamEnabled = false;

  const localTime = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  function addActivity(message, kind = "info") {
    const item = document.createElement("li");
    item.className = kind;
    const copy = document.createElement("span");
    copy.textContent = message;
    const time = document.createElement("small");
    time.textContent = localTime();
    item.append(copy, time);
    activityList.prepend(item);
    while (activityList.children.length > 8) activityList.lastElementChild.remove();
  }
  function persist() {
    try { localStorage.setItem(STORAGE_KEY, serializeConversation(messages, modeInput.value)); } catch { /* private mode */ }
  }
  function restore() {
    let stored = null;
    try { stored = deserializeConversation(localStorage.getItem(STORAGE_KEY)); } catch { stored = null; }
    if (!stored) return false;
    messages.splice(0, messages.length, ...stored.messages);
    if ([...modeInput.options].some((option) => option.value === stored.mode)) modeInput.value = stored.mode;
    return messages.length > 0;
  }
  function setBusy(isBusy) {
    pending = isBusy;
    sendButton.disabled = isBusy;
    stopButton.hidden = !isBusy;
  }
  function setCoreState({ connected, title, detail }) {
    corePanel.classList.toggle("online", connected === true);
    corePanel.classList.toggle("offline", connected === false);
    coreState.textContent = title;
    coreDetail.textContent = detail;
    runtimeStatus.textContent = detail;
    providerSummary.textContent = detail;
    providerState.textContent = connected === true ? "Online" : connected === false ? "Offline" : "Checking";
    backendPill.textContent = connected === true ? "Core connected" : connected === false ? "Model offline" : "Checking backend";
    backendPill.classList.toggle("online", connected === true);
    backendPill.classList.toggle("offline", connected === false);
  }
  function actionButton(label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.action = action;
    button.textContent = label;
    return button;
  }
  function renderMessage(message, index) {
    const article = document.createElement("article");
    article.className = `message ${message.role}${message.status === "streaming" ? " streaming" : ""}`;
    article.dataset.index = String(index);
    const label = document.createElement("span");
    label.textContent = message.role === "assistant" ? "VERONICA" : message.role === "system" ? "SYSTEM" : "YOU";
    const body = document.createElement("div");
    body.className = "message-body";
    if (message.role === "assistant" && message.status !== "streaming") body.innerHTML = markdownToSafeHtml(message.content);
    else body.textContent = message.content;
    article.append(label, body);
    if (message.status === "error" && message.error) {
      const error = document.createElement("p");
      error.className = "message-error";
      error.textContent = message.error;
      article.append(error);
    }
    const last = index === messages.length - 1;
    const actions = document.createElement("div");
    actions.className = "message-actions";
    if (message.content) actions.append(actionButton("Copy", "copy"));
    if (!pending && last && message.role === "user") actions.append(actionButton("Retry", "retry"));
    if (!pending && last && message.role === "assistant" && message.status === "error") actions.append(actionButton("Retry", "retry"));
    if (!pending && last && message.role === "assistant" && message.status !== "error") actions.append(actionButton("Regenerate", "regenerate"));
    if (actions.childElementCount) article.append(actions);
    conversation.append(article);
  }
  function renderConversation() {
    conversation.replaceChildren();
    if (!messages.length) {
      const article = document.createElement("article");
      article.className = "message system";
      article.innerHTML = `<span>SYSTEM</span><p>${escapeHtml(WELCOME)}</p>`;
      conversation.append(article);
    } else {
      messages.forEach(renderMessage);
    }
    conversation.scrollTop = conversation.scrollHeight;
  }
  async function refreshCapabilities() {
    try {
      const data = await fetch("/api/capabilities", { cache: "no-store" }).then((response) => response.json());
      streamEnabled = Array.isArray(data.implemented) && data.implemented.includes("streaming_chat");
    } catch {
      streamEnabled = false;
    }
  }
  async function refreshHealth({ announce = false } = {}) {
    try {
      const response = await fetch("/api/health", { cache: "no-store" });
      const data = await response.json();
      const connected = Boolean(data.provider?.model_available);
      const detail = connected ? "Veronica Core is connected to its configured model server." : "Wrapper ready; the model server is not connected yet.";
      setCoreState({ connected, title: connected ? "Core connected" : "Wrapper ready", detail });
      if (announce) addActivity(connected ? "Live health check confirmed the model server." : "Live health check confirmed wrapper-only mode.", connected ? "success" : "info");
    } catch {
      setCoreState({ connected: false, title: "Wrapper unavailable", detail: "The local Veronica wrapper could not be reached." });
      if (announce) addActivity("Health check could not reach the local wrapper.", "error");
    }
    await refreshCapabilities();
  }
  function historyForRequest() {
    return messages.filter((item) => item.role === "user" || (item.role === "assistant" && item.status !== "error" && item.status !== "streaming")).map(({ role, content }) => ({ role, content }));
  }
  async function readSse(response, assistant, id) {
    if (!response.body) throw new Error("The model provider returned an empty stream.");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const data = trimmed.slice(5).trim();
        if (!data || data === "[DONE]") continue;
        let payload;
        try { payload = JSON.parse(data); } catch { continue; }
        if (payload?.error) {
          const message = typeof payload.error === "string" ? payload.error : payload.error.message;
          throw new Error(message || "The model provider returned a stream error.");
        }
        const delta = payload?.choices?.[0]?.delta?.content;
        if (typeof delta === "string" && delta) {
          assistant.content += delta;
          if (id === generation) {
            const body = conversation.querySelector(".message.assistant:last-of-type .message-body");
            if (body) body.textContent = assistant.content;
            conversation.scrollTop = conversation.scrollHeight;
          }
        }
      }
    }
  }
  async function requestCompletion() {
    if (pending) return;
    await refreshCapabilities();
    const id = ++generation;
    const assistant = { role: "assistant", content: "", status: "streaming" };
    messages.push(assistant);
    abortController = new AbortController();
    setBusy(true);
    renderConversation();
    persist();
    notice.textContent = "Veronica is waiting for the model server…";
    try {
      const response = await fetch("/v1/chat/completions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: abortController.signal,
        body: JSON.stringify({
          model: "Veronica",
          messages: historyForRequest(),
          veronica_mode: modeInput.value,
          stream: streamEnabled,
        }),
      });
      if (!response.ok) {
        let detail = "Chat request was rejected.";
        try {
          const data = await response.json();
          if (typeof data.detail === "string") detail = data.detail;
        } catch { /* non-JSON error */ }
        throw new Error(detail);
      }
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("text/event-stream")) {
        await readSse(response, assistant, id);
      } else {
        const data = await response.json();
        const answer = data.choices?.[0]?.message?.content;
        if (!answer) throw new Error("The model returned no assistant message.");
        assistant.content = answer;
      }
      if (!assistant.content) throw new Error("The model returned no assistant message.");
      assistant.status = "complete";
      addActivity("Received a Veronica response.", "success");
      notice.textContent = "Model alias: Veronica";
    } catch (error) {
      if (error.name === "AbortError") {
        assistant.status = assistant.content ? "stopped" : "error";
        if (!assistant.content) assistant.error = "Generation stopped.";
        addActivity("Generation stopped.", "info");
        notice.textContent = "Generation stopped";
      } else {
        assistant.status = "error";
        assistant.error = error.message;
        addActivity(`Chat request failed: ${error.message}`, "error");
        notice.textContent = "Provider check required";
      }
    } finally {
      if (abortController) abortController = null;
      if (id === generation) {
        setBusy(false);
        renderConversation();
        persist();
        refreshHealth();
      }
    }
  }
  function dropTrailingAssistant() {
    while (messages.length && messages[messages.length - 1].role === "assistant") messages.pop();
  }
  async function retryOrRegenerate() {
    if (pending) return;
    dropTrailingAssistant();
    if (!messages.length || messages[messages.length - 1].role !== "user") return;
    persist();
    renderConversation();
    await requestCompletion();
  }
  async function copyMessage(index) {
    const item = messages[index];
    if (!item?.content) return;
    try {
      await navigator.clipboard.writeText(item.content);
      notice.textContent = "Copied";
      addActivity("Copied a message.", "success");
    } catch {
      notice.textContent = "Copy failed";
      addActivity("Copy failed.", "error");
    }
  }
  function resetConversation() {
    generation += 1;
    if (abortController) abortController.abort();
    abortController = null;
    setBusy(false);
    messages.length = 0;
    persist();
    renderConversation();
    notice.textContent = "Model alias: Veronica";
    addActivity("Started a new local conversation.");
    promptInput.focus();
  }

  conversation.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const article = button.closest(".message");
    const index = Number(article?.dataset.index);
    const action = button.dataset.action;
    if (action === "copy") copyMessage(index);
    if (action === "retry" || action === "regenerate") retryOrRegenerate();
  });
  composer.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (pending) return;
    const content = promptInput.value.trim();
    if (!content) return;
    messages.push({ role: "user", content });
    promptInput.value = "";
    persist();
    renderConversation();
    addActivity("Message sent to Veronica.");
    await requestCompletion();
  });
  stopButton.addEventListener("click", () => { if (abortController) abortController.abort(); });
  promptInput.addEventListener("keydown", (event) => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") composer.requestSubmit(); });
  modeInput.addEventListener("change", persist);
  document.querySelector("#refreshStatus").addEventListener("click", () => refreshHealth({ announce: true }));
  document.querySelector("#newConversation").addEventListener("click", resetConversation);
  function drawStarfield() {
    const canvas = document.querySelector("#starfield");
    const context = canvas.getContext("2d");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let stars = [];
    const resize = () => {
      canvas.width = window.innerWidth * devicePixelRatio;
      canvas.height = window.innerHeight * devicePixelRatio;
      context.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
      stars = Array.from({ length: Math.min(130, Math.ceil(window.innerWidth / 11)) }, () => ({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        size: Math.random() * 1.4 + .25,
        alpha: Math.random() * .6 + .15,
      }));
    };
    const render = () => {
      context.clearRect(0, 0, window.innerWidth, window.innerHeight);
      for (const star of stars) {
        context.fillStyle = `rgba(221, 198, 255, ${star.alpha})`;
        context.fillRect(star.x, star.y, star.size, star.size);
      }
      if (!reduceMotion) requestAnimationFrame(render);
    };
    resize();
    window.addEventListener("resize", resize);
    render();
  }
  document.querySelector("#clock").textContent = localTime();
  window.setInterval(() => { document.querySelector("#clock").textContent = localTime(); }, 1000);
  drawStarfield();
  const restored = restore();
  renderConversation();
  addActivity(restored ? "Restored the previous local conversation." : "Veronica v4 chat interface loaded.");
  refreshHealth();
  window.setInterval(refreshHealth, 15000);
}

if (typeof document !== "undefined") bootChat();
if (typeof module === "object" && module.exports) {
  module.exports = { escapeHtml, markdownToSafeHtml, serializeConversation, deserializeConversation, STORAGE_KEY };
}
