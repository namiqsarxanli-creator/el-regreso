/* --------------------------------------------------------------------
 * El Regreso — canlı qraf.
 * Serverdən gələn hər hadisə bir node-u işıqlandırır; altar və şam
 * göstəricisi state-dən doldurulur. Heç bir kitabxana yoxdur.
 * ------------------------------------------------------------------ */

const SVG_NS = "http://www.w3.org/2000/svg";
const canvas = document.getElementById("canvas");

/* --- qrafın topologiyası (solution/graph.py ilə eyni) ---------------- */
const NODES = [
  { id: "dusk_angelitos",  x:  92, y: 132, label: "qürub · 1 noy", kind: "saf funksiya" },
  { id: "dusk_difuntos",   x:  92, y: 246, label: "qürub · 2 noy", kind: "saf funksiya" },
  { id: "read_ofrenda",    x: 232, y: 189, label: "altarı oxu",    kind: "tool" },
  { id: "follow_petals",   x: 372, y: 189, label: "ləçək yolu",    kind: "command" },
  { id: "lost",            x: 372, y: 330, label: "azdı",          kind: "loop" },
  { id: "wait_for_family", x: 218, y: 330, label: "ailəni gözlə",  kind: "interrupt" },
  { id: "mictlan_crossing",x: 524, y: 189, label: "Mictlán keçidi",kind: "subqraf", big: true },
  { id: "taste_food",      x: 686, y:  96, label: "dad",           kind: "paralel" },
  { id: "smell_copal",     x: 686, y: 189, label: "copal",         kind: "paralel" },
  { id: "see_photos",      x: 686, y: 282, label: "şəkil",         kind: "paralel" },
  { id: "reunion",         x: 812, y: 189, label: "görüş",         kind: "fan-in" },
  { id: "judge_ofrenda",   x: 916, y:  92, label: "qiymət",        kind: "llm · sxem" },
  { id: "write_calaverita",x: 916, y: 189, label: "calaverita",    kind: "llm" },
  { id: "speak_to_family", x: 1020, y: 140, label: "söz",          kind: "llm" },
  { id: "farewell",        x: 1020, y: 282, label: "vida",         kind: "saf funksiya" },
  { id: "third_death",     x: 1020, y: 392, label: "üçüncü ölüm",  kind: "son" },
];

const EDGES = [
  ["START", "dusk_angelitos", "thin"],
  ["START", "dusk_difuntos", "thin"],
  ["dusk_angelitos", "read_ofrenda", "petal"],
  ["dusk_difuntos", "read_ofrenda", "petal"],
  ["read_ofrenda", "follow_petals", "petal"],
  ["follow_petals", "mictlan_crossing", "petal"],
  ["follow_petals", "lost", "thin"],
  ["lost", "wait_for_family", "thin"],
  ["lost", "farewell", "thin"],
  ["wait_for_family", "follow_petals", "petal"],
  ["mictlan_crossing", "taste_food", "petal"],
  ["mictlan_crossing", "smell_copal", "petal"],
  ["mictlan_crossing", "see_photos", "petal"],
  ["taste_food", "reunion", "petal"],
  ["smell_copal", "reunion", "petal"],
  ["see_photos", "reunion", "petal"],
  ["reunion", "judge_ofrenda", "petal"],
  ["reunion", "write_calaverita", "petal"],
  ["judge_ofrenda", "speak_to_family", "petal"],
  ["write_calaverita", "speak_to_family", "petal"],
  ["speak_to_family", "farewell", "petal"],
  ["farewell", "third_death", "thin"],
  ["farewell", "END", "thin"],
];

const ANCHORS = { START: { x: 26, y: 189 }, END: { x: 1114, y: 282 } };

/* --- əşya nişanları --------------------------------------------------- */
const GLYPH = {
  flower: '<circle cx="8" cy="8" r="2.4"/><g fill="none" stroke="currentColor" stroke-width="1.3"><path d="M8 1.6c1.8 1 1.8 3 0 4M8 14.4c-1.8-1-1.8-3 0-4M1.6 8c1-1.8 3-1.8 4 0M14.4 8c-1 1.8-3 1.8-4 0"/></g>',
  water:  '<path d="M8 1.5 C11 6 13 8 13 10.4 A5 5 0 0 1 3 10.4 C3 8 5 6 8 1.5Z" fill="none" stroke="currentColor" stroke-width="1.3"/>',
  bread:  '<ellipse cx="8" cy="9" rx="6" ry="4.6" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M8 4.6v8.8M5 5.6l6 6.8M11 5.6l-6 6.8" stroke="currentColor" stroke-width="1"/>',
  candle: '<rect x="6" y="6" width="4" height="8.5" rx="1" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M8 5.4c1.6-1.2.4-2.6 0-3.4-.6 1-1.7 2.2 0 3.4Z"/>',
  smoke:  '<path d="M6 14c0-3 4-3 4-6s-3-3-2-6" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M10.5 13.5c0-2 2-2.4 2-4" fill="none" stroke="currentColor" stroke-width="1"/>',
  photo:  '<rect x="2.5" y="3.5" width="11" height="9" rx="1.4" fill="none" stroke="currentColor" stroke-width="1.3"/><circle cx="6.4" cy="7" r="1.2"/><path d="M4 11l3-3 2.4 2.2L11 8.8l1.2 1.4" fill="none" stroke="currentColor" stroke-width="1.1"/>',
  bottle: '<path d="M6.6 1.8h2.8v2.6l1.8 2.6v7H4.8v-7l1.8-2.6z" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M4.8 9.6h6.4" stroke="currentColor" stroke-width="1"/>',
  skull:  '<path d="M8 1.8a5.4 5.4 0 0 0-5.4 5.4c0 2 1 3 1 4.4V13h8.8v-1.4c0-1.4 1-2.4 1-4.4A5.4 5.4 0 0 0 8 1.8Z" fill="none" stroke="currentColor" stroke-width="1.3"/><circle cx="6" cy="7.4" r="1.2"/><circle cx="10" cy="7.4" r="1.2"/>',
  cup:    '<path d="M3.5 5h8v4.5a4 4 0 0 1-8 0Z" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M11.5 6h1.6a1.6 1.6 0 0 1 0 3.2h-1.6" fill="none" stroke="currentColor" stroke-width="1.1"/>',
  fruit:  '<circle cx="8" cy="9.4" r="4.4" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M8 5V2.6M8 3.4c1.4-.6 2.6-.4 3.2.2" fill="none" stroke="currentColor" stroke-width="1.1"/>',
  salt:   '<path d="M3 13.2 8 3l5 10.2Z" fill="none" stroke="currentColor" stroke-width="1.3"/>',
  dot:    '<circle cx="8" cy="8" r="2.6"/>',
};

const ITEM = {
  "cempasúchil": ["flower", "cielo"],
  "su": ["water", "inframundo"],
  "duz": ["salt", "inframundo"],
  "pan de muerto": ["bread", "tierra"],
  "copal": ["smoke", "cielo"],
  "şam": ["candle", "cielo"],
  "şəkil": ["photo", "cielo"],
  "mezcal": ["bottle", "inframundo"],
  "siqaret": ["smoke", "inframundo"],
  "tamales": ["bread", "tierra"],
  "qəhvə": ["cup", "tierra"],
  "süd": ["cup", "tierra"],
  "şokolad": ["bread", "tierra"],
  "şəkər kəllə": ["skull", "tierra"],
  "oyuncaq": ["dot", "tierra"],
  "meyvə": ["fruit", "tierra"],
};

/* --- qrafın çəkilməsi -------------------------------------------------- */
const nodeEls = {};
const edgeEls = {};

function center(id) {
  if (ANCHORS[id]) return ANCHORS[id];
  const n = NODES.find((n) => n.id === id);
  return { x: n.x, y: n.y };
}

function edgePath(from, to) {
  const a = center(from), b = center(to);
  const dx = b.x - a.x, dy = b.y - a.y;
  const curve = Math.abs(dy) > 30 ? 0.45 : 0.18;
  const c1 = { x: a.x + dx * curve + 26, y: a.y };
  const c2 = { x: b.x - dx * curve - 26, y: b.y };
  return `M ${a.x} ${a.y} C ${c1.x} ${c1.y} ${c2.x} ${c2.y} ${b.x} ${b.y}`;
}

function el(tag, attrs, parent) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, v);
  if (parent) parent.appendChild(node);
  return node;
}

function drawGraph() {
  canvas.innerHTML = "";
  const edgeLayer = el("g", {}, canvas);
  const nodeLayer = el("g", {}, canvas);

  for (const [from, to, style] of EDGES) {
    const p = el("path", { d: edgePath(from, to), class: `edge ${style}` }, edgeLayer);
    edgeEls[`${from}->${to}`] = p;
  }

  for (const anchor of ["START", "END"]) {
    const { x, y } = ANCHORS[anchor];
    const g = el("g", { class: "node anchor" }, nodeLayer);
    el("circle", { cx: x, cy: y, r: 13 }, g);
    el("text", { x, y: y + 27, class: "kind" }, g).textContent = anchor;
  }

  for (const n of NODES) {
    const w = n.big ? 128 : 104, h = n.big ? 58 : 46;
    const g = el("g", { class: `node${n.big ? " sub" : ""}`, id: `n-${n.id}` }, nodeLayer);
    el("rect", { x: n.x - w / 2, y: n.y - h / 2, width: w, height: h, rx: 11 }, g);
    el("rect", { x: n.x - w / 2, y: n.y - h / 2, width: w, height: h, rx: 11, class: "pulse" }, g);
    el("text", { x: n.x, y: n.y - 6 }, g).textContent = n.label;
    el("text", { x: n.x, y: n.y + 11, class: "kind" }, g).textContent = n.kind;
    nodeEls[n.id] = g;
  }

  const steps = el("text", { x: 524, y: 232, class: "crossing-steps", id: "crossing-steps" }, canvas);
  steps.textContent = "";
}

const done = new Set();

function resetGraph() {
  done.clear();
  Object.values(nodeEls).forEach((g) => (g.setAttribute("class", g.classList.contains("sub") ? "node sub" : "node")));
  Object.values(edgeEls).forEach((p) => p.classList.remove("lit"));
  document.getElementById("crossing-steps").textContent = "";
}

function activate(id) {
  const g = nodeEls[id];
  if (!g) return;
  g.classList.add("active");
  for (const [key, path] of Object.entries(edgeEls)) {
    const [from, to] = key.split("->");
    if (to === id && (done.has(from) || from === "START")) path.classList.add("lit");
  }
  setTimeout(() => {
    g.classList.remove("active");
    g.classList.add(id === "third_death" ? "dead" : "done");
    done.add(id);
    if (id === "farewell") edgeEls["farewell->END"]?.classList.add("lit");
  }, 520);
}

/* --- panellər --------------------------------------------------------- */
let lastAltar = [];

function renderAltar(items) {
  const tiers = { cielo: [], tierra: [], inframundo: [] };
  (items || []).forEach((item) => {
    const [glyph, tier] = ITEM[item] || ["dot", "tierra"];
    tiers[tier].push([item, glyph]);
  });
  for (const [tier, list] of Object.entries(tiers)) {
    const box = document.getElementById(`tier-${tier}`);
    box.innerHTML = "";
    list.forEach(([item, glyph]) => {
      const fresh = lastAltar.length && !lastAltar.includes(item);
      box.insertAdjacentHTML(
        "beforeend",
        `<span class="item${fresh ? " fresh" : ""}">
           <svg viewBox="0 0 16 16" fill="currentColor">${GLYPH[glyph]}</svg>${item}
         </span>`
      );
    });
  }
  document.getElementById("altar-count").textContent = `${(items || []).length} əşya`;
  lastAltar = [...(items || [])];
}

/* --- LangGraph jurnalı ------------------------------------------------ */
function logLine(text, kind = "node") {
  const box = document.getElementById("log");
  const li = document.createElement("li");
  li.className = kind;
  li.textContent = text;
  box.appendChild(li);
  box.scrollTop = box.scrollHeight;
  while (box.children.length > 200) box.removeChild(box.firstChild);
}

function clearLog() {
  document.getElementById("log").innerHTML = "";
}

/* Bir node icrasının tam kartı: nə etdi → state-ə nə yazdı → kimə ötürür */
function logFlow(m) {
  const box = document.getElementById("log");
  const li = document.createElement("li");
  li.className = "entry";
  li.innerHTML = `
    <div class="e-head">
      <span class="e-no">${String(m.step).padStart(2, "0")}</span>
      <b>${esc(m.label)}</b>
      <em>${esc(m.role || "")}</em>
    </div>
    ${m.did ? `<div class="e-did">${esc(m.did)}</div>` : ""}
    ${m.wrote ? `<div class="e-wrote"><span>state</span>${esc(m.wrote)}</div>` : ""}
    ${m.note ? `<div class="e-note">${esc(m.note)}</div>` : ""}
    ${m.next ? `<div class="e-next"><span>növbəti</span>${esc(m.next)}</div>` : ""}
    <code class="e-api">${esc(m.api || "")}</code>`;
  box.appendChild(li);
  box.scrollTop = box.scrollHeight;
  while (box.children.length > 60) box.removeChild(box.firstChild);
}

function esc(s) {
  return String(s).replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" }[c]));
}

function renderVerdict(values) {
  const box = document.getElementById("verdict");
  const j = values.judgement;
  if (!j || !Object.keys(j).length) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  document.getElementById("warmth-value").textContent = j.warmth ?? "—";
  document.getElementById("verdict-text").textContent = j.verdict || "";
  document.getElementById("longing-text").textContent =
    j.longing ? `ən çox darıxdığı: ${j.longing}` : "";
}

function renderCalaverita(values) {
  const box = document.getElementById("calaverita");
  if (!values.calaverita) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  document.getElementById("calaverita-text").textContent = values.calaverita.trim();
}

function renderVoices(values) {
  const voices = values.voices || [];
  const badge = document.getElementById("voice-badge");
  if (!voices.length) {
    badge.textContent = "";
    return;
  }
  // Hamısı eyni modeldirsə, bir dəfə yazırıq.
  const models = [...new Set(voices.map((v) => v.split("←").pop().trim()))];
  badge.textContent = models.join(" · ");
}

function renderMemory(values) {
  const rem = values.remembrance ?? 0;
  document.getElementById("rem-value").textContent = rem;
  const wax = document.getElementById("wax");
  wax.style.height = `${rem}%`;
  wax.style.background = rem > 60
    ? "linear-gradient(180deg,#F6E4C8,#D9B98A)"
    : rem > 25
    ? "linear-gradient(180deg,#F0A035,#B9702A)"
    : "linear-gradient(180deg,#E23F6C,#7A2038)";
  document.getElementById("flame").style.opacity = rem > 0 ? 1 : 0;
  const visits = values.visits || [];
  document.getElementById("rem-note").textContent = visits.length
    ? `${visits.length} ildir xatırlanır`
    : "";

  const words = document.getElementById("words");
  if (values.words) {
    words.hidden = false;
    words.textContent = values.words;
  }

  const list = document.getElementById("visits");
  list.innerHTML = "";
  visits.slice().reverse().forEach((v) => {
    list.insertAdjacentHTML(
      "beforeend",
      `<li><span class="dot ${v.arrived ? "" : "miss"}"></span>
         <span class="yr">${v.year}</span>
         <span class="of">${(v.ofrenda || []).join(", ") || "boş altar"}</span></li>`
    );
  });
}

let history = [];
let selected = null;

function renderHistory(rows) {
  history = rows || [];
  const box = document.getElementById("dots");
  box.innerHTML = "";
  history.slice().reverse().forEach((row) => {
    const dot = document.createElement("div");
    dot.className = "cp" + (row.next.includes("__start__") ? " year-edge" : "");
    dot.title = `${row.year ?? "—"} · növbəti: ${row.next.join(", ") || "son"} · xat. ${row.remembrance ?? "—"}`;
    dot.onclick = () => selectCheckpoint(row, dot);
    box.appendChild(dot);
  });
}

function selectCheckpoint(row, dot) {
  document.querySelectorAll(".cp.selected").forEach((d) => d.classList.remove("selected"));
  dot.classList.add("selected");
  selected = row;
  const form = document.getElementById("fork");
  form.hidden = false;
  document.getElementById("fork-label").textContent =
    `${row.year ?? "—"} ili · növbəti: ${row.next.join(", ") || "son"}`;
}

function toast(text) {
  const div = document.createElement("div");
  div.className = "toast";
  div.textContent = text;
  document.body.appendChild(div);
  setTimeout(() => div.remove(), 3200);
}

/* --- papel picado ------------------------------------------------------ */
(function papel() {
  const colors = ["#E23F6C", "#F0A035", "#2FA08C", "#8455C0", "#EFD05A"];
  const flags = document.getElementById("flags");
  for (let i = 0; i < 18; i++) {
    const g = document.createElementNS(SVG_NS, "g");
    g.setAttribute("class", "flag");
    g.setAttribute("transform", `translate(${i * 70} 3)`);
    g.style.animationDelay = `${(i % 5) * 0.4}s`;
    const use = document.createElementNS(SVG_NS, "use");
    use.setAttribute("href", "#flag");
    use.setAttribute("fill", colors[i % colors.length]);
    use.setAttribute("opacity", ".78");
    g.appendChild(use);
    flags.appendChild(g);
  }
})();

/* --- WebSocket --------------------------------------------------------- */
let ws;
function connect() {
  ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  ws.onmessage = (event) => handle(JSON.parse(event.data));
  ws.onclose = () => setTimeout(connect, 1200);
}

function handle(msg) {
  const status = document.getElementById("graph-status");
  switch (msg.type) {
    case "start":
      resetGraph();
      clearLog();
      document.getElementById("ask").hidden = true;
      status.textContent = `${msg.year} — gecə başladı`;
      break;
    case "api":
      logLine(msg.line, msg.kind);
      break;
    case "flow":
      logFlow(msg);
      break;
    case "fork":
      resetGraph();
      status.textContent = "paralel budaq";
      renderAltar(msg.ofrenda);
      break;
    case "node":
      activate(msg.node);
      status.textContent = msg.node;
      if (msg.update.ofrenda) renderAltar(msg.update.ofrenda);
      if (msg.update.crossing_steps) {
        document.getElementById("crossing-steps").textContent =
          msg.update.crossing_steps.slice(-1)[0] || "";
      }
      if (msg.update.crossing_report) {
        document.getElementById("crossing-steps").textContent = msg.update.crossing_report;
      }
      break;
    case "interrupt":
      document.getElementById("ask").hidden = false;
      document.getElementById("ask-text").textContent = msg.payload.question;
      document.getElementById("ask-hint").textContent = msg.payload.hint;
      document.getElementById("ask-input").focus();
      status.textContent = "insan gözlənilir";
      break;
    case "done":
      renderAltar(msg.values.ofrenda);
      renderMemory(msg.values);
      renderVerdict(msg.values);
      renderCalaverita(msg.values);
      renderVoices(msg.values);
      renderHistory(msg.history);
      status.textContent = msg.values.forgotten ? "üçüncü ölüm" : "gecə bitdi";
      if (msg.values.forgotten) toast("Xatırlanma sıfıra düşdü — thread silinməlidir.");
      break;
    case "forgotten":
      resetGraph();
      renderAltar([]);
      renderMemory({ remembrance: 0, visits: [] });
      renderVerdict({});
      renderCalaverita({});
      renderVoices({});
      renderHistory([]);
      document.getElementById("words").hidden = true;
      toast("Thread silindi. Növbəti il heç kim gəlməyəcək.");
      break;
    case "error":
      toast(msg.message);
      break;
  }
}

/* --- idarəetmə --------------------------------------------------------- */
async function loadSouls() {
  const souls = await (await fetch("/api/souls")).json();
  const soulSel = document.getElementById("soul");
  soulSel.innerHTML = souls
    .map((s) => `<option value="${s.name}">${s.display} · ${s.kind}</option>`)
    .join("");
  soulSel.onchange = () => {
    const soul = souls.find((s) => s.name === soulSel.value);
    document.getElementById("year").innerHTML = soul.years
      .map((y) => `<option>${y}</option>`)
      .join("");
    loadState();
  };
  soulSel.onchange();
}

async function loadState() {
  const soul = document.getElementById("soul").value;
  const data = await (await fetch(`/api/state/${soul}`)).json();
  lastAltar = [];
  renderAltar(data.values.ofrenda || []);
  renderMemory(data.values);
  renderVerdict(data.values);
  renderCalaverita(data.values);
  renderVoices(data.values);
  renderHistory(data.history);
  document.getElementById("words").hidden = !data.values.words;
  if (data.waiting.length) {
    document.getElementById("graph-status").textContent =
      `yarımçıq: ${data.waiting.join(", ")}`;
  }
}

document.getElementById("run").onclick = () => {
  ws.send(JSON.stringify({
    action: "run",
    soul: document.getElementById("soul").value,
    year: document.getElementById("year").value,
  }));
};

document.getElementById("forget").onclick = () => {
  ws.send(JSON.stringify({ action: "forget", soul: document.getElementById("soul").value }));
};

document.getElementById("ask-form").onsubmit = (e) => {
  e.preventDefault();
  const input = document.getElementById("ask-input");
  ws.send(JSON.stringify({
    action: "resume",
    soul: document.getElementById("soul").value,
    gift: input.value.trim(),
  }));
  input.value = "";
  document.getElementById("ask").hidden = true;
};

document.getElementById("fork").onsubmit = (e) => {
  e.preventDefault();
  if (!selected) return;
  const gifts = document.getElementById("fork-gift").value
    .split(",").map((s) => s.trim()).filter(Boolean);
  ws.send(JSON.stringify({
    action: "fork",
    soul: document.getElementById("soul").value,
    checkpoint: selected.id,
    gifts,
  }));
  document.getElementById("fork").hidden = true;
};

document.getElementById("fork-cancel").onclick = () => {
  document.getElementById("fork").hidden = true;
  document.querySelectorAll(".cp.selected").forEach((d) => d.classList.remove("selected"));
};

drawGraph();
connect();

