const API_BASE_URL =
  window.location.protocol !== "file:" &&
  (window.location.port === "" || window.location.port === "80")
    ? "/api"
    : "http://localhost:8000";

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const previewEl = document.getElementById("preview");
const titleEl = document.getElementById("title");
const sendBtn = document.getElementById("send-btn");
const modelSelect = document.getElementById("model-select");
const clearGraphBtn = document.getElementById("clear-graph-btn");
const statusEl = document.getElementById("status");

let currentText = "";
let currentFileName = "";
let statusTimeout;

let networkInstance = null;

async function renderGraph() {
  try {
    const res = await fetch(`${API_BASE_URL}/graphs`);
    if (!res.ok) return;
    const data = await res.json();

    const graphSection = document.getElementById("graph-section");

    if (!data || !data.relations || data.relations.length === 0) {
      graphSection.style.display = "none";
      return;
    }

    const nodeMap = new Map();
    let nodeId = 1;

    for (const rel of data.relations) {
      if (!nodeMap.has(rel.entity_1)) nodeMap.set(rel.entity_1, nodeId++);
      if (!nodeMap.has(rel.entity_2)) nodeMap.set(rel.entity_2, nodeId++);
    }

    const nodes = new vis.DataSet(
      [...nodeMap.entries()].map(([label, id]) => ({ id, label }))
    );

    const edges = new vis.DataSet(
      data.relations.map((rel, i) => ({
        id: i,
        from: nodeMap.get(rel.entity_1),
        to: nodeMap.get(rel.entity_2),
        label: rel.relation,
        arrows: "to",
      }))
    );

    const options = {
      nodes: {
        shape: "dot",
        size: 14,
        color: {
          background: "#3b82f6",
          border: "#60a5fa",
          highlight: { background: "#60a5fa", border: "#93c5fd" },
        },
        font: { color: "#e5e5e5", size: 13 },
      },
      edges: {
        color: { color: "#555", highlight: "#aaaaaa" },
        font: { color: "#aaaaaa", size: 11, align: "middle" },
        smooth: { type: "dynamic" },
      },
      physics: {
        stabilization: { iterations: 150 },
        barnesHut: { gravitationalConstant: -5000, springLength: 120 },
      },
      interaction: { hover: true, tooltipDelay: 100 },
    };

    graphSection.style.display = "block";

    if (networkInstance) {
      networkInstance.destroy();
    }
    networkInstance = new vis.Network(
      document.getElementById("graph-container"),
      { nodes, edges },
      options
    );
  } catch (err) {
    console.error("Failed to render graph:", err);
  }
}

async function fetchGraphVersion() {
  try {
    const res = await fetch(`${API_BASE_URL}/graphs`);
    if (!res.ok) return null;
    const data = await res.json();
    return data ? data.version : null;
  } catch {
    return null;
  }
}

async function pollForGraphUpdate(versionBefore) {
  const INTERVAL_MS = 1500;
  const TIMEOUT_MS = 60000;
  const started = Date.now();

  setStatus("Article saved. Waiting for graph update...", "info");

  return new Promise((resolve) => {
    const interval = setInterval(async () => {
      if (Date.now() - started > TIMEOUT_MS) {
        clearInterval(interval);
        setStatus("Article saved. Graph update is taking longer than expected.", "ok");
        resolve();
        return;
      }

      const version = await fetchGraphVersion();
      if (version !== null && version !== versionBefore) {
        clearInterval(interval);
        setStatus(`Graph updated to version ${version}.`, "ok");
        resolve();
      }
    }, INTERVAL_MS);
  });
}

async function fetchCurrentModel() {
  try {
    const res = await fetch(`${API_BASE_URL}/model`);
    const data = await res.json();
    modelSelect.value = data.model;
  } catch (err) {
    console.error("Failed to fetch current model:", err);
  }
}

modelSelect.addEventListener("change", async () => {
  try {
    await fetch(`${API_BASE_URL}/model`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: modelSelect.value }),
    });
  } catch (err) {
    console.error("Failed to set model:", err);
  }
});

fetchCurrentModel();
renderGraph();

// na start blokujemy przycisk
sendBtn.disabled = true;

function resetStatus() {
  clearTimeout(statusTimeout);
  statusEl.textContent = "";
  statusEl.className = "";
}

function setStatus(message, type) {
  clearTimeout(statusTimeout);

  statusEl.textContent = message;
  statusEl.className = type;

  statusTimeout = setTimeout(() => {
    statusEl.textContent = "";
    statusEl.className = "";
  }, 5000);
}

function handleFile(file) {
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".txt")) {
    setStatus("Only .txt files are handled", "error");
    return;
  }

  resetStatus();

  const reader = new FileReader();
  reader.onload = (e) => {
    currentText = e.target.result || "";
    currentFileName = file.name;

    previewEl.textContent =
      currentText.slice(0, 1000) + (currentText.length > 1000 ? "…" : "");

    titleEl.innerHTML = `<span>${file.name.replace(/\.txt$/i, "").trim()}</span>`;

    sendBtn.disabled = currentText.trim().length === 0;
  };

  reader.readAsText(file, "utf-8");
}

dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", (event) => {
  const file = event.target.files[0];
  handleFile(file);
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragover");
  const file = event.dataTransfer.files[0];
  handleFile(file);
});

sendBtn.addEventListener("click", async () => {
  resetStatus();

  if (!currentFileName) {
    setStatus("No file selected", "error");
    return;
  }

  const title = currentFileName.replace(/\.txt$/i, "").trim();

  if (!currentText.trim()) {
    setStatus("Lack of content, file empty?", "error");
    return;
  }

  sendBtn.disabled = true;
  sendBtn.textContent = "Processing request...";
  previewEl.textContent = "";
  titleEl.textContent = "";

  try {
    const versionBefore = await fetchGraphVersion();

    const response = await fetch(`${API_BASE_URL}/articles`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: title,
        text: currentText,
      }),
    });

    const data = await response.json();
    console.log("Response data:", data);

    if (!response.ok) {
      throw new Error(data.detail || "Error HTTP " + response.status);
    }

    await pollForGraphUpdate(versionBefore);
    await renderGraph();
  } catch (err) {
    console.error(err);
    setStatus("Error processing request: " + err.message, "error");
  } finally {
    sendBtn.disabled = true;
    sendBtn.textContent = "Send";
  }
});

clearGraphBtn.addEventListener("click", async () => {
  resetStatus();

  clearGraphBtn.disabled = true;
  clearGraphBtn.textContent = "Clearing...";

  try {
    const response = await fetch(`${API_BASE_URL}/graphs/clean`, {
      method: "DELETE",
    });

    if (!response.ok) {
      let errorMessage = "Error HTTP " + response.status;

      try {
        const data = await response.json();
        errorMessage = data.detail || errorMessage;
      } catch {
        // brak jsona w odpowiedzi
      }

      throw new Error(errorMessage);
    }

    currentText = "";
    currentFileName = "";
    previewEl.textContent = "";
    titleEl.textContent = "";
    fileInput.value = "";
    sendBtn.disabled = true;

    setStatus("Knowledge graph deleted", "ok");
    document.getElementById("graph-section").style.display = "none";
    if (networkInstance) {
      networkInstance.destroy();
      networkInstance = null;
    }
  } catch (err) {
    console.error(err);
    setStatus("Error deleting graph: " + err.message, "error");
  } finally {
    clearGraphBtn.disabled = false;
    clearGraphBtn.textContent = "Clear graph";
  }
});
