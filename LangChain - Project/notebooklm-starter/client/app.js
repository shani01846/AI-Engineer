// NotebookLM-style client. Talks to the FastAPI backend only over /api.

const api = {
  async get(url) {
    const r = await fetch(url);
    if (!r.ok) throw await err(r);
    return r.json();
  },

  async send(method, url, body) {
    const r = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) throw await err(r);
    return r.status === 204 ? null : r.json();
  },
};
async function err(r) {
  let detail = r.statusText;
  try {
    detail = (await r.json()).detail || detail;
  } catch {}
  const e = new Error(detail);
  e.status = r.status;
  return e;
}

// One conversation thread per page load. "New chat" starts a fresh one so the agent's
// short-term memory resets.
const state = {
  sources: [],
  threadId: crypto.randomUUID(),
  pendingApproval: null
};const $ = (id) => document.getElementById(id);
const SUGGESTIONS = [
  "What drove Acme's gross margin improvement in Q2 2024?",
  "Compare Fleet OS growth between Q1 and Q2.",
  "What are the key risks to the subscription strategy?",
];

function formatToolLabel(tool) {
  return tool.replace(/_/g, " ");
}

function escapeHtml(s) {
  return String(s).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}

/* ---- sources --------------------------------------------------------------- */

async function loadSources() {
  state.sources = await api.get("/api/sources");
  renderSources();
}
function showApproval(data) {

  clearEmptyState();

  const div = document.createElement("div");

  div.className = "msg ai";

  const approval_type = data.approval?.approval_type || "scrape_confirmation";
  const urls = data.approval?.urls || [];

  if (approval_type === "source_selection") {
    // Source selection UI with checkboxes
    let html = `
      <div>
        <strong>🔗 Found ${urls.length} potential sources</strong>
      </div>
      <div style="margin: 10px 0; font-size: 14px;">
        Select which sources to add to your notebook:
      </div>
    `;

    html += '<div style="margin: 10px 0;">';

    urls.forEach((url, idx) => {
      html += `
        <label style="display: block; margin: 8px 0; cursor: pointer;">
          <input type="checkbox" class="url-checkbox" data-url="${escapeHtml(url)}" checked />
          <span style="margin-left: 8px;">${escapeHtml(url.substring(0, 60))}${url.length > 60 ? '…' : ''}</span>
        </label>
      `;
    });

    html += '</div>';

    html += `
      <button class="approve-btn" style="margin-right: 8px;">
        ✅ Add Selected
      </button>

      <button class="reject-btn">
        ❌ Cancel
      </button>
    `;

    div.innerHTML = html;

    div.querySelector(".approve-btn")
      .onclick = () => {
        const checkboxes = div.querySelectorAll(".url-checkbox:checked");
        const selected = Array.from(checkboxes).map(cb => cb.dataset.url);
        approveAction("approve", selected);
      };

    div.querySelector(".reject-btn")
      .onclick = () => approveAction("reject", []);

  } else {
    // Scrape confirmation UI
    let html = `
      <div>
        <strong>🔎 Sources found</strong>
      </div>
    `;

    if(urls.length){

      html += "<ul>";

      urls.forEach(url=>{
        html += `
          <li>
            ${escapeHtml(url)}
          </li>
        `;
      });

      html += "</ul>";
    }

    html += `
      <div>
        Add these sources to notebook?
      </div>

      <button class="approve-btn">
        ✅ Approve
      </button>

      <button class="reject-btn">
        ❌ Reject
      </button>
    `;

    div.innerHTML = html;

    div.querySelector(".approve-btn")
      .onclick = ()=>approveAction("approve");

    div.querySelector(".reject-btn")
      .onclick = ()=>approveAction("reject");
  }

  $("messages").appendChild(div);

  $("messages").scrollTop =
      $("messages").scrollHeight;
}
async function approveAction(decision, selected_urls = []){


  const pending = addMessage(
    "ai",
    "Processing approval..."
  );


  try {

    const body = {
      thread_id: state.threadId,
      decision: decision
    };

    if (selected_urls && selected_urls.length > 0) {
      body.selected_urls = selected_urls;
    }

    const data = await api.send(
      "POST",
      "/api/chat/approve",
      body
    );


    pending.remove();


    if(data.answer){

      decorateAnswer(
        addMessage("ai",""),
        {
          answer:data.answer,
          citations:data.citations || []
        }
      );

    }


    await loadSources();


  }
  catch(e){

    pending.remove();

    addMessage(
      "system",
      "⚠ " + e.message
    );
  }

}
function renderSources() {
  const ul = $("sources");
  ul.innerHTML = "";
  const activeCount = state.sources.filter((s) => s.active).length;
  $("active-count").textContent = `${activeCount} active`;
  $("select-all").checked = activeCount === state.sources.length && state.sources.length > 0;

  for (const s of state.sources) {
    const li = document.createElement("li");
    if (!s.active) li.className = "inactive";
    li.innerHTML = `
      <input type="checkbox" ${s.active ? "checked" : ""} />
      <span class="s-name" title="${escapeHtml(s.name)}">${escapeHtml(s.name)}</span>
      <span class="s-meta">${s.chars.toLocaleString()}</span>
      <button class="icon-btn" title="View">👁</button>
      <button class="icon-btn danger" title="Remove">✕</button>`;
    const [chk, , , viewBtn, delBtn] = li.children;
    chk.onchange = () => toggleSource(s.id, chk.checked);
    viewBtn.onclick = () => viewSource(s.id);
    delBtn.onclick = () => deleteSource(s.id);
    ul.appendChild(li);
  }
}

async function toggleSource(id, active) {
  await api.send("PATCH", `/api/sources/${id}`, { active });
  await loadSources();
}
async function deleteSource(id) {
  await api.send("DELETE", `/api/sources/${id}`);
  await loadSources();
}
async function viewSource(id) {
  const s = await api.get(`/api/sources/${id}`);
  openViewer(s.name, s.content);
}

async function addText(e) {
  e.preventDefault();
  const content = $("add-content").value.trim();
  if (!content) return;
  await api.send("POST", "/api/sources", { name: $("add-name").value, content });
  $("add-name").value = "";
  $("add-content").value = "";
  $("add-form").classList.add("hidden");
  await loadSources();
}

async function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch("/api/sources/upload", { method: "POST", body: fd });
  if (!r.ok) {
    addMessage("system", `⚠ ${(await err(r)).message}`);
    return;
  }
  $("add-form").classList.add("hidden");
  await loadSources();
}

async function selectAll(checked) {
  await Promise.all(
    state.sources
      .filter((s) => s.active !== checked)
      .map((s) => api.send("PATCH", `/api/sources/${s.id}`, { active: checked }))
  );
  await loadSources();
}

/* ---- chat ------------------------------------------------------------------ */

function renderEmptyState() {
  const m = $("messages");
  if (m.children.length) return;
  const div = document.createElement("div");
  div.className = "empty";
  div.innerHTML = `
    <div>Ask anything about your active sources — answers are grounded and cited.</div>
    <div class="suggestions">${SUGGESTIONS.map(
      (q) => `<button class="suggestion">${escapeHtml(q)}</button>`
    ).join("")}</div>`;
  div.querySelectorAll(".suggestion").forEach((b, i) => {
    b.onclick = () => {
      $("chat-input").value = SUGGESTIONS[i];
      $("chat-form").requestSubmit();
    };
  });
  m.appendChild(div);
}

function clearEmptyState() {
  const e = $("messages").querySelector(".empty");
  if (e) e.remove();
}

const AGENT_TOOL_SEQUENCE = [
  "search_sources",
  "web_search",
  "request_source_approval",
  "scrape_source",
  "crawl_source",
  "search_sources",
];

function addPendingAgentMessage() {
  clearEmptyState();
  const div = document.createElement("div");
  div.className = "msg ai pending";

  const header = document.createElement("div");
  header.className = "agent-status";
  header.innerHTML = "<strong>Agent is working</strong>";

  const list = document.createElement("div");
  list.className = "agent-tool-list";

  const toolEls = [];
  AGENT_TOOL_SEQUENCE.forEach((tool, index) => {
    const pill = document.createElement("span");
    pill.className = `tool-pill ${index === 0 ? "active" : ""}`;
    pill.textContent = formatToolLabel(tool);
    list.appendChild(pill);
    toolEls.push(pill);
  });

  div.appendChild(header);
  div.appendChild(list);
  $("messages").appendChild(div);
  $("messages").scrollTop = $("messages").scrollHeight;

  let index = 0;
  const interval = setInterval(() => {
    toolEls.forEach((el, i) => {
      el.classList.toggle("active", i === index);
      el.classList.toggle("done", i < index);
    });
    index = (index + 1) % toolEls.length;
  }, 650);

  div.dataset.activityInterval = String(interval);

  const liveLabel = document.createElement("div");
  liveLabel.className = "agent-live-label";
  liveLabel.textContent = "Using: search_sources";
  div.appendChild(liveLabel);

  return div;
}

function stopPendingAgentMessage(div) {
  if (!div) return;
  const interval = Number(div.dataset.activityInterval || 0);
  if (interval) clearInterval(interval);
  div.classList.remove("pending");
}

function addMessage(role, text, { pending = false } = {}) {
  clearEmptyState();
  const div = document.createElement("div");
  div.className = `msg ${role}${pending ? " pending" : ""}`;
  div.textContent = text;
  $("messages").appendChild(div);
  $("messages").scrollTop = $("messages").scrollHeight;
  return div;
}

function decorateAnswer(div, data) {
  div.className = "msg ai";
  div.textContent = data.answer;

  const meta = document.createElement("div");
  meta.className = "meta";

  const parts = [];

  if (data.citations?.length) {
    parts.push(
      `<div><span class="label">sources:</span> ${data.citations
        .map((c) => `<span class="chip">${escapeHtml(c.source)}</span>`)
        .join("")}</div>`
    );
  }

  if (data.tools_used?.length) {
    parts.push(
      `<div><span class="label">tools:</span> ${data.tools_used
        .map((tool) => `<span class="chip tool-chip">${escapeHtml(formatToolLabel(tool))}</span>`)
        .join("")}</div>`
    );
  }

  if (parts.length) {
    meta.innerHTML = parts.join("");
    div.appendChild(meta);
  }

  const actions = document.createElement("div");
  actions.className = "msg-actions";
  const save = document.createElement("button");
  save.className = "link-btn";
  save.textContent = "＋ Save to note";
  save.onclick = () => saveNote(data.answer);
  actions.appendChild(save);
  div.appendChild(actions);
}

async function sendMessage(message) {
  addMessage("user", message);
  const pending = addPendingAgentMessage();
  $("send").disabled = true;
  try {
    const data = await api.send(
  "POST",
  "/api/chat",
  {
    message,
    thread_id: state.threadId,
  }
);



stopPendingAgentMessage(pending);
pending.remove();



if(data.interrupt){

    // Save thread ID for approval
    state.threadId = data.thread_id || state.threadId;

    // Show the interrupt message
    if(data.answer){
        addMessage("ai", data.answer);
    }

    // Show approval UI
    showApproval({
        approval: data.approval,
        threadId: data.thread_id
    });

}
else if(
    data.answer
){

    decorateAnswer(
        addMessage("ai",""),
        data
    );

}
  } catch (e) {
    pending.remove();
    addMessage("system", `⚠ ${e.message}`);
  } finally {
    $("send").disabled = false;
    $("messages").scrollTop = $("messages").scrollHeight;
  }
}

/* ---- studio + notes -------------------------------------------------------- */

async function loadArtifacts() {
  const arts = await api.get("/api/studio/artifacts");
  const grid = $("artifacts");
  grid.innerHTML = "";
  for (const a of arts) {
    const btn = document.createElement("button");
    btn.className = "artifact";
    const badge = a.status === "planned" ? `<span class="a-badge">Soon</span>` : "";
    btn.innerHTML = `<span class="a-icon">${a.icon}</span>
      <span class="a-title">${escapeHtml(a.title)}</span>${badge}`;
    btn.onclick = () => generateArtifact(a);
    grid.appendChild(btn);
  }
}

async function generateArtifact(a) {
  const pending = addMessage("ai", `Generating ${a.title}…`, { pending: true });
  try {
    const note = await api.send("POST", "/api/studio/generate", { kind: a.key });
    pending.remove();
    decorateAnswer(addMessage("ai", ""), { answer: note.content, citations: [] });
    await loadNotes();
  } catch (e) {
    pending.remove();
    addMessage("system", `⚠ ${e.message}`);
  }
}

async function loadNotes() {
  renderNotes(await api.get("/api/notes"));
}
function renderNotes(notes) {
  const ul = $("notes");
  ul.innerHTML = "";
  if (!notes.length) {
    ul.innerHTML = `<div class="note-empty">No notes yet — save a grounded answer.</div>`;
    return;
  }
  for (const n of notes) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="n-title" title="${escapeHtml(n.title)}">${escapeHtml(
      n.title
    )}</span><button class="icon-btn danger">✕</button>`;
    li.querySelector("button").onclick = async () => {
      await api.send("DELETE", `/api/notes/${n.id}`);
      loadNotes();
    };
    li.querySelector(".n-title").onclick = () => openViewer(n.title, n.content);
    ul.appendChild(li);
  }
}
async function saveNote(content) {
  const title = content.split("\n")[0].slice(0, 50);
  await api.send("POST", "/api/notes", { title, content });
  loadNotes();
}

/* ---- viewer modal ---------------------------------------------------------- */

function openViewer(title, content) {
  $("viewer-title").textContent = title;
  $("viewer-content").textContent = content;
  $("viewer").classList.remove("hidden");
  $("overlay").classList.remove("hidden");
}
function closeViewer() {
  $("viewer").classList.add("hidden");
  $("overlay").classList.add("hidden");
}

/* ---- wiring ---------------------------------------------------------------- */

$("add-toggle").onclick = () => $("add-form").classList.toggle("hidden");
$("add-cancel").onclick = () => $("add-form").classList.add("hidden");
$("add-form").addEventListener("submit", addText);
$("add-file").onchange = (e) => e.target.files[0] && uploadFile(e.target.files[0]);
$("select-all").onchange = (e) => selectAll(e.target.checked);

$("chat-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const msg = $("chat-input").value.trim();
  if (!msg) return;
  $("chat-input").value = "";
  sendMessage(msg);
});

$("new-chat").onclick = () => {
  state.threadId = crypto.randomUUID(); // fresh memory
  $("messages").innerHTML = "";
  renderEmptyState();
};

$("close-viewer").onclick = closeViewer;
$("overlay").onclick = closeViewer;

/* ---- init ------------------------------------------------------------------ */

(async function init() {
  await Promise.all([loadSources(), loadArtifacts(), loadNotes()]);
  renderEmptyState();
})();
