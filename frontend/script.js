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
const loadLatestBtn = document.getElementById("load-latest-btn");
const statusEl = document.getElementById("status");
const manualToggleBtn = document.getElementById("manual-toggle-btn");
const manualModal = document.getElementById("manual-modal");
const manualTitleInput = document.getElementById("manual-title");
const manualRelationsInput = document.getElementById("manual-relations");
const manualSaveBtn = document.getElementById("manual-save-btn");
const manualCancelBtn = document.getElementById("manual-cancel-btn");
const manualCancelBtn2 = document.getElementById("manual-cancel-btn2");
const manualFileInput = document.getElementById("manual-file-input");
const manualFileName = document.getElementById("manual-file-name");

let currentText = "";
let currentFileName = "";
let statusTimeout;
let sortDirection = "desc";

const NEW_EDGE_HIGHLIGHT_MS = 15000;

let networkInstance = null;
let knownEdgeMap = null;   // Map<edgeKey, rel>
let knownNodeLabels = null; // Set<label>
let activeGraphId = null;  // null = always latest

const edgeKey = (rel) => `${rel.entity_1}|${rel.relation}|${rel.entity_2}`;

async function renderGraph(highlightNew = false, graphId = null) {
  try {
    const url = graphId != null
      ? `${API_BASE_URL}/graphs/${graphId}`
      : `${API_BASE_URL}/graphs`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();

    const graphSection = document.getElementById("graph-section");

    if (!data || !data.relations || data.relations.length === 0) {
      if (graphId != null) {
        graphSection.style.display = "block";
        if (networkInstance) { networkInstance.destroy(); networkInstance = null; }
        document.getElementById("graph-container").innerHTML =
          "<div style='display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:13px;'>This version has no relations</div>";
      } else {
        graphSection.style.display = "none";
      }
      return;
    }

    const nodeMap = new Map();
    let nodeId = 1;

    for (const rel of data.relations) {
      if (!nodeMap.has(rel.entity_1)) nodeMap.set(rel.entity_1, nodeId++);
      if (!nodeMap.has(rel.entity_2)) nodeMap.set(rel.entity_2, nodeId++);
    }

    const currentNodeLabels = new Set(nodeMap.keys());
    const currentEdgeMap = new Map(data.relations.map(rel => [edgeKey(rel), rel]));

    // diff — co zniknęło
    const removedNodes = knownNodeLabels
      ? [...knownNodeLabels].filter(l => !currentNodeLabels.has(l))
      : [];
    const removedEdges = knownEdgeMap
      ? [...knownEdgeMap.values()].filter(rel => !currentEdgeMap.has(edgeKey(rel)))
      : [];

    const nodesData = [...nodeMap.entries()].map(([label, id]) => {
      const isNew = highlightNew && !knownNodeLabels?.has(label);
      return {
        id,
        label,
        ...(isNew && {
          color: {
            background: "#22c55e",
            border: "#4ade80",
            highlight: { background: "#4ade80", border: "#86efac" },
          },
        }),
      };
    });

    knownNodeLabels = currentNodeLabels;
    const nodes = new vis.DataSet(nodesData);

    const edgesData = data.relations.map((rel, i) => {
      const isNew = highlightNew && !knownEdgeMap?.has(edgeKey(rel));
      return {
        id: i,
        from: nodeMap.get(rel.entity_1),
        to: nodeMap.get(rel.entity_2),
        label: rel.relation,
        arrows: "to",
        ...(isNew && {
          color: { color: "#22c55e", highlight: "#4ade80" },
          font: { color: "#e5e5e5", size: 11, align: "middle", strokeWidth: 0, background: "#0f2d1a" },
        }),
      };
    });

    knownEdgeMap = currentEdgeMap;
    const edges = new vis.DataSet(edgesData);

    const options = {
      nodes: {
        shape: "box",
        color: {
          background: "#3b82f6",
          border: "#60a5fa",
          highlight: { background: "#60a5fa", border: "#93c5fd" },
        },
        font: { color: "#e5e5e5", size: 13 },
        margin: 8,
        borderWidth: 1,
      },
      edges: {
        color: { color: "#555", highlight: "#aaaaaa" },
        font: { color: "#e5e5e5", size: 11, align: "middle", strokeWidth: 0, background: "#1e1e1e" },
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

    if (highlightNew) {
      // zielone — reset po timeoucie
      const newEdgeIds = edgesData.filter(e => e.color).map(e => e.id);
      const newNodeIds = nodesData.filter(n => n.color).map(n => n.id);
      if (newEdgeIds.length > 0 || newNodeIds.length > 0) {
        setTimeout(() => {
          if (newEdgeIds.length > 0) edges.update(newEdgeIds.map(id => ({ id, color: null, font: null })));
          if (newNodeIds.length > 0) nodes.update(newNodeIds.map(id => ({ id, color: null })));
        }, NEW_EDGE_HIGHLIGHT_MS);
      }

      // czerwone — phantom usunięte węzły i krawędzie
      if (removedNodes.length > 0 || removedEdges.length > 0) {
        const allNodeIdMap = new Map(nodeMap);
        const phantomNodeItems = removedNodes.map(label => {
          const phantomId = "ph_" + label;
          allNodeIdMap.set(label, phantomId);
          return {
            id: phantomId,
            label,
            color: { background: "#ef4444", border: "#f87171", highlight: { background: "#f87171", border: "#fca5a5" } },
          };
        });
        const phantomEdgeItems = removedEdges.map(rel => ({
          id: "ph_" + edgeKey(rel),
          from: allNodeIdMap.get(rel.entity_1),
          to: allNodeIdMap.get(rel.entity_2),
          label: rel.relation,
          arrows: "to",
          dashes: true,
          color: { color: "#ef4444", highlight: "#f87171" },
          font: { color: "#e5e5e5", size: 11, align: "middle", strokeWidth: 0, background: "#2d1515" },
        }));

        if (phantomNodeItems.length > 0) nodes.add(phantomNodeItems);
        if (phantomEdgeItems.length > 0) edges.add(phantomEdgeItems);

        setTimeout(() => {
          edges.remove(phantomEdgeItems.map(e => e.id));
          nodes.remove(phantomNodeItems.map(n => n.id));
        }, NEW_EDGE_HIGHLIGHT_MS);
      }
    }
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
  const TIMEOUT_MS = 180000;
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

      try {
        const statusRes = await fetch(`${API_BASE_URL}/status`);
        if (statusRes.ok) {
          const status = await statusRes.json();
          if (status.error) {
            clearInterval(interval);
            setStatus("Error: " + status.error, "error");
            resolve();
            return;
          }
        }
      } catch {}

      const version = await fetchGraphVersion();
      if (version !== null && version !== versionBefore) {
        clearInterval(interval);
        activeGraphId = null;
        setStatus(`Graph updated to version ${version}.`, "ok");
        await fetchGraphList();
        resolve();
      }
    }, INTERVAL_MS);
  });
}

async function fetchLocalModels() {
  const group = document.getElementById("local-models-group");
  try {
    const res = await fetch(`${API_BASE_URL}/local-models`);
    const data = await res.json();
    group.innerHTML = "";
    if (data.models && data.models.length > 0) {
      data.models.forEach(modelId => {
        const opt = document.createElement("option");
        opt.value = `local:${modelId}`;
        opt.textContent = modelId;
        group.appendChild(opt);
      });
    } else {
      group.innerHTML = '<option disabled value="">Not available</option>';
    }
  } catch (err) {
    console.error("Failed to fetch local models:", err);
    group.innerHTML = '<option disabled value="">Not available</option>';
  }
}

function formatGraphDate(isoStr) {
  const dt = new Date(isoStr);
  const day = String(dt.getDate()).padStart(2, "0");
  const month = String(dt.getMonth() + 1).padStart(2, "0");
  const hour = String(dt.getHours()).padStart(2, "0");
  const min = String(dt.getMinutes()).padStart(2, "0");
  return `${day}.${month} ${hour}:${min}`;
}

async function fetchGraphList() {
  const container = document.getElementById("graph-history");
  try {
    const res = await fetch(`${API_BASE_URL}/graphs/all`);
    console.log("[graphs/all] status:", res.status);
    if (!res.ok) {
      container.innerHTML = '<div class="graph-history-empty">Unavailable</div>';
      return;
    }
    const graphs = await res.json();
    console.log("[graphs/all] data:", graphs);

    const nonEmpty = graphs ? graphs.filter(g => g.relation_count > 0) : [];

    container.innerHTML = "";

    if (nonEmpty.length === 0) {
      container.innerHTML = '<div class="graph-history-empty">No graphs yet</div>';
      return;
    }

    const sorted = [...nonEmpty].sort((a, b) => {
      const ap = a.position ?? Infinity, bp = b.position ?? Infinity;
      if (ap !== bp) return sortDirection === "desc" ? bp - ap : ap - bp;
      return sortDirection === "desc" ? b.version - a.version : a.version - b.version;
    });

    const header = document.createElement("div");
    header.className = "graph-history-header";
    header.innerHTML =
      `<span class="graph-header-pos" style="width:36px;flex-shrink:0;cursor:pointer;user-select:none;text-align:right">Pos.</span>` +
      `<span style="width:84px;flex-shrink:0">Date</span>` +
      `<span style="flex:1">Article</span>` +
      `<span style="width:100px;flex-shrink:0">Model</span>` +
      `<span style="width:28px;text-align:right;flex-shrink:0">#</span>` +
      `<span style="width:16px;flex-shrink:0"></span>` +
      `<span style="width:16px;flex-shrink:0"></span>`;
    header.querySelector(".graph-header-pos").addEventListener("click", () => {
      sortDirection = sortDirection === "desc" ? "asc" : "desc";
      fetchGraphList();
    });
    container.appendChild(header);

    sorted.forEach((g, index) => {
      const isActive = activeGraphId != null
        ? g.graph_id === activeGraphId
        : index === 0;

      const item = document.createElement("div");
      item.className = "graph-item" + (isActive ? " active" : "");
      item.dataset.graphId = g.graph_id;

      const modelLabel = g.model
        ? g.model.replace(/^local:/, "").split("/").pop()
        : "—";
      const posLabel = g.position ?? "—";
      item.innerHTML =
        `<span class="graph-item-position" role="button" title="Click to set position">${posLabel}</span>` +
        `<span class="graph-item-meta">${formatGraphDate(g.created_at)}</span>` +
        `<span class="graph-item-title">${g.title ?? "—"}</span>` +
        `<span class="graph-item-model">${modelLabel}</span>` +
        `<span class="graph-item-count nonzero">${g.relation_count}</span>` +
        `<span class="graph-item-export" role="button" title="Export .txt" data-id="${g.graph_id}">&#8595;</span>` +
        `<span class="graph-item-delete" role="button" title="Delete" data-id="${g.graph_id}">&times;</span>`;


      item.addEventListener("click", () => {
        activeGraphId = g.graph_id;
        document.querySelectorAll(".graph-item").forEach(el =>
          el.classList.toggle("active", parseInt(el.dataset.graphId) === activeGraphId)
        );
        setStatus(`v${g.version} · ${formatGraphDate(g.created_at)} · ${g.relation_count} relations`, "info");
        renderGraph(false, g.graph_id);
      });

      item.querySelector(".graph-item-position").addEventListener("click", (e) => {
        e.stopPropagation();
        const span = e.currentTarget;
        const input = document.createElement("input");
        input.type = "number";
        input.value = g.position ?? "";
        input.className = "graph-item-position-input";
        input.placeholder = "—";
        span.replaceWith(input);
        input.focus();
        input.select();
        const save = async () => {
          const newPos = parseInt(input.value);
          if (!isNaN(newPos) && newPos !== g.position) {
            try {
              const res = await fetch(`${API_BASE_URL}/graphs/${g.graph_id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ position: newPos }),
              });
              if (!res.ok) throw new Error("HTTP " + res.status);
            } catch (err) {
              setStatus("Failed to update position: " + err.message, "error");
            }
          }
          await fetchGraphList();
        };
        input.addEventListener("keydown", (e) => {
          if (e.key === "Enter") { e.preventDefault(); save(); }
          if (e.key === "Escape") input.replaceWith(span);
        });
        input.addEventListener("blur", save);
      });

      item.querySelector(".graph-item-export").addEventListener("click", async (e) => {
        e.stopPropagation();
        try {
          const res = await fetch(`${API_BASE_URL}/graphs/${g.graph_id}`);
          if (!res.ok) return;
          const data = await res.json();
          if (!data?.relations?.length) return;
          const lines = data.relations.map(r => `${r.entity_1} -> ${r.relation} -> ${r.entity_2}`);
          const blob = new Blob([lines.join("\n")], { type: "text/plain" });
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = (g.title ?? `graph_v${g.version}`) + ".txt";
          a.click();
          URL.revokeObjectURL(a.href);
        } catch (err) {
          setStatus("Export failed: " + err.message, "error");
        }
      });

      item.querySelector(".graph-item-delete").addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm(`Delete v${g.version} — ${g.title ?? "untitled"}?`)) return;
        const wasActive = activeGraphId === g.graph_id;
        try {
          const res = await fetch(`${API_BASE_URL}/graphs/${g.graph_id}`, { method: "DELETE" });
          if (!res.ok) throw new Error("HTTP " + res.status);
          if (wasActive) {
            activeGraphId = null;
            knownEdgeMap = null;
            knownNodeLabels = null;
          }
          await fetchGraphList();
          if (wasActive) renderGraph(false);
        } catch (err) {
          setStatus("Error deleting graph: " + err.message, "error");
        }
      });

      container.appendChild(item);
    });
  } catch (err) {
    console.error("Failed to fetch graph list:", err);
  }
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

function closeManualModal() {
  manualModal.classList.add("hidden");
  manualTitleInput.value = "";
  manualRelationsInput.value = "";
  manualFileInput.value = "";
  manualFileName.textContent = "";
}


manualFileInput.addEventListener("change", () => {
  const file = manualFileInput.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    manualRelationsInput.value = e.target.result.trim();
    manualFileName.textContent = file.name;
    if (!manualTitleInput.value.trim()) {
      manualTitleInput.value = file.name.replace(/\.txt$/i, "").trim();
    }
  };
  reader.readAsText(file, "utf-8");
});

manualToggleBtn.addEventListener("click", () => manualModal.classList.remove("hidden"));
manualCancelBtn.addEventListener("click", closeManualModal);
manualCancelBtn2.addEventListener("click", closeManualModal);
manualModal.addEventListener("click", (e) => { if (e.target === manualModal) closeManualModal(); });

manualSaveBtn.addEventListener("click", async () => {
  const relationsText = manualRelationsInput.value.trim();
  if (!relationsText) {
    setStatus("Enter at least one relation", "error");
    return;
  }

  manualSaveBtn.disabled = true;
  manualSaveBtn.textContent = "Saving...";

  try {
    const res = await fetch(`${API_BASE_URL}/graphs/manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: manualTitleInput.value.trim() || "manual",
        relations_text: relationsText,
      }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "HTTP " + res.status);
    }

    const saved = await res.json();
    activeGraphId = saved.graph_id;
    closeManualModal();
    setStatus(`Graph v${saved.version} saved (${saved.relations.length} relations)`, "ok");
    await fetchGraphList();
    await renderGraph(false, saved.graph_id);
  } catch (err) {
    setStatus("Error saving graph: " + err.message, "error");
  } finally {
    manualSaveBtn.disabled = false;
    manualSaveBtn.textContent = "Save graph";
  }
});

loadLatestBtn.addEventListener("click", async () => {
  activeGraphId = null;
  knownEdgeMap = null;
  knownNodeLabels = null;
  await fetchGraphList();
  await renderGraph(false);
});

const compareBtn = document.getElementById("compare-btn");
const evalModal = document.getElementById("eval-modal");
const evalCloseBtn = document.getElementById("eval-close-btn");
const evalRunBtn = document.getElementById("eval-run-btn");
const evalResults = document.getElementById("eval-results");

let graphListCache = [];

async function openEvalModal() {
  evalResults.innerHTML = "";
  evalModal.classList.remove("hidden");

  const [graphsRes, promptsRes] = await Promise.all([
    fetch(`${API_BASE_URL}/graphs/all`),
    fetch(`${API_BASE_URL}/prompts`),
  ]);
  const graphs = await graphsRes.json();
  const prompts = await promptsRes.json();

  graphListCache = (graphs || []).filter(g => g.relation_count > 0);

  const selGraph = document.getElementById("eval-graph-a");
  selGraph.innerHTML = "";
  graphListCache.forEach(g => {
    const opt = document.createElement("option");
    opt.value = g.graph_id;
    const modelLabel = g.model ? g.model.replace(/^local:/, "").split("/").pop() : "—";
    opt.textContent = `[${g.position ?? "—"}] ${g.title ?? "—"} · ${modelLabel}`;
    selGraph.appendChild(opt);
  });

  const selPrompt = document.getElementById("eval-prompt");
  selPrompt.innerHTML = "";
  (prompts || []).forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.key;
    opt.textContent = p.label;
    selPrompt.appendChild(opt);
  });
}

compareBtn.addEventListener("click", openEvalModal);

document.getElementById("eval-file-input").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (ev) => {
    document.getElementById("eval-text").value = ev.target.result;
  };
  reader.readAsText(file);
  e.target.value = "";
});

evalCloseBtn.addEventListener("click", () => evalModal.classList.add("hidden"));
evalModal.addEventListener("click", (e) => { if (e.target === evalModal) evalModal.classList.add("hidden"); });

evalRunBtn.addEventListener("click", async () => {
  const graphId = parseInt(document.getElementById("eval-graph-a").value);
  const promptKey = document.getElementById("eval-prompt").value;
  const text = document.getElementById("eval-text").value.trim();

  if (!graphId) {
    evalResults.innerHTML = "<div style='color:var(--error);font-size:13px;'>Select a graph.</div>";
    return;
  }
  if (!promptKey) {
    evalResults.innerHTML = "<div style='color:var(--error);font-size:13px;'>Select a prompt.</div>";
    return;
  }
  if (!text) {
    evalResults.innerHTML = "<div style='color:var(--error);font-size:13px;'>Paste the source text.</div>";
    return;
  }

  evalRunBtn.disabled = true;
  evalRunBtn.textContent = "Running...";
  evalResults.innerHTML = "<div style='color:var(--text-muted);font-size:13px;'>Evaluating graph...</div>";

  try {
    const res = await fetch(`${API_BASE_URL}/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ graph_id: graphId, text, prompt_key: promptKey }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    evalResults.innerHTML =
      `<div style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">` +
      `Graph: ${data.graph_relations} relations</div>` +
      `<div style="font-size:13px;white-space:pre-wrap;line-height:1.7;color:var(--text);">${data.analysis}</div>`;
  } catch (err) {
    evalResults.innerHTML = `<div style='color:var(--error);font-size:13px;'>Error: ${err.message}</div>`;
  } finally {
    evalRunBtn.disabled = false;
    evalRunBtn.textContent = "Run";
  }
});

fetchLocalModels().then(fetchCurrentModel);
fetchGraphList();
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
    await renderGraph(true);
  } catch (err) {
    console.error(err);
    setStatus("Error processing request: " + err.message, "error");
  } finally {
    currentText = "";
    currentFileName = "";
    fileInput.value = "";
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

    activeGraphId = null;
    setStatus("Knowledge graph deleted", "ok");
    document.getElementById("graph-section").style.display = "none";
    fetchGraphList();
    if (networkInstance) {
      networkInstance.destroy();
      networkInstance = null;
    }
    knownEdgeMap = null;
    knownNodeLabels = null;

  } catch (err) {
    console.error(err);
    setStatus("Error deleting graph: " + err.message, "error");
  } finally {
    clearGraphBtn.disabled = false;
    clearGraphBtn.textContent = "Clear graph";
  }
});
