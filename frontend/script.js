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
const evalHistoryList = document.getElementById("eval-history-list");
const evalDetailModal = document.getElementById("eval-detail-modal");
const evalDetailClose = document.getElementById("eval-detail-close-btn");
const evalDetailSubtitle = document.getElementById("eval-detail-subtitle");
const evalDetailContent = document.getElementById("eval-detail-content");

let graphListCache = [];

function buildEvalResultHtml(data) {
  const pct = v => (v * 100).toFixed(1) + "%";
  const metricColor = v => v >= 0.7 ? "var(--success)" : v >= 0.4 ? "var(--warning)" : "var(--error)";
  const rateColor = v => v <= 0.3 ? "var(--success)" : v <= 0.6 ? "var(--warning)" : "var(--error)";

  const metricsHtml = `
    <div style="display:flex;gap:12px;margin-bottom:16px;">
      ${[["Precision", data.precision], ["Recall", data.recall], ["F1", data.f1]].map(([label, val]) => `
        <div style="flex:1;background:var(--bg-lighter);border:1px solid var(--border);border-radius:8px;padding:10px 14px;text-align:center;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">${label}</div>
          <div style="font-size:22px;font-weight:700;color:${metricColor(val)};">${pct(val)}</div>
        </div>`).join("")}
      <div style="flex:1;background:var(--bg-lighter);border:1px solid var(--border);border-radius:8px;padding:10px 14px;text-align:center;">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Hallucinated</div>
        <div style="font-size:22px;font-weight:700;color:${metricColor(1 - data.unsupported_count / data.graph_relations)};">${data.unsupported_count}/${data.graph_relations}</div>
      </div>
      ${data.connectivity_score != null ? `
      <div style="flex:1;background:var(--bg-lighter);border:1px solid var(--border);border-radius:8px;padding:10px 14px;text-align:center;">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Connectivity</div>
        <div style="font-size:22px;font-weight:700;color:${metricColor(data.connectivity_score)};">${pct(data.connectivity_score)}</div>
      </div>` : ""}
    </div>`;

  const refMetricsHtml = (data.t_precision != null) ? `
    <div style="margin-bottom:6px;font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Reference graph comparison (graph #${data.reference_graph_id})</div>
    <div style="display:flex;gap:12px;margin-bottom:16px;">
      ${[["T-Precision", data.t_precision, metricColor], ["T-Recall", data.t_recall, metricColor], ["T-F1", data.t_f1, metricColor]].map(([label, val, color]) => `
        <div style="flex:1;background:var(--bg-lighter);border:1px solid var(--border);border-radius:8px;padding:10px 14px;text-align:center;">
          <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">${label}</div>
          <div style="font-size:22px;font-weight:700;color:${color(val)};">${pct(val)}</div>
        </div>`).join("")}
      <div style="flex:1;background:var(--bg-lighter);border:1px solid var(--border);border-radius:8px;padding:10px 14px;text-align:center;">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Unmatched</div>
        <div style="font-size:22px;font-weight:700;color:${rateColor(data.hallucination_rate)};">${pct(data.hallucination_rate)}</div>
      </div>
      <div style="flex:1;background:var(--bg-lighter);border:1px solid var(--border);border-radius:8px;padding:10px 14px;text-align:center;">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Missing</div>
        <div style="font-size:22px;font-weight:700;color:${rateColor(data.omission_rate)};">${pct(data.omission_rate)}</div>
      </div>
      <div style="flex:1;background:var(--bg-lighter);border:1px solid var(--border);border-radius:8px;padding:10px 14px;text-align:center;">
        <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">GED</div>
        <div style="font-size:22px;font-weight:700;color:var(--text);">${data.ged}</div>
      </div>
    </div>` : "";

  const verdictsHtml = data.triple_verdicts?.length ? `
    <div style="margin-bottom:14px;">
      <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Triples</div>
      <div style="border:1px solid var(--border);border-radius:6px;overflow:hidden;">
        ${data.triple_verdicts.map(v => `
          <div style="display:flex;align-items:flex-start;gap:10px;padding:6px 10px;border-bottom:1px solid var(--border);font-size:12px;">
            <span style="flex-shrink:0;color:${v.supported ? "var(--success)" : "var(--error)"};">${v.supported ? "✓" : "✕"}</span>
            <span style="flex:1;color:var(--text);font-family:monospace;">${v.triple}</span>
            ${v.comment ? `<span style="color:var(--text-muted);font-size:11px;max-width:200px;">${v.comment}</span>` : ""}
          </div>`).join("")}
      </div>
    </div>` : "";

  const missingHtml = data.missing_relations?.length ? `
    <div style="margin-bottom:14px;">
      <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Missing (${data.missing_count})</div>
      <div style="border:1px solid var(--border);border-radius:6px;overflow:hidden;">
        ${data.missing_relations.map(r => `
          <div style="padding:6px 10px;border-bottom:1px solid var(--border);font-size:12px;color:var(--warning);font-family:monospace;">${r}</div>`).join("")}
      </div>
    </div>` : "";

  const analysisHtml = `
    <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">Analysis</div>
    <div style="font-size:13px;white-space:pre-wrap;line-height:1.7;color:var(--text);">${data.analysis}</div>`;

  return metricsHtml + refMetricsHtml + verdictsHtml + missingHtml + analysisHtml;
}

async function loadEvalHistory() {
  evalHistoryList.innerHTML = "<div style='color:var(--text-muted);font-size:12px;'>Loading...</div>";
  const res = await fetch(`${API_BASE_URL}/evaluations`);
  const items = await res.json();

  if (!items.length) {
    evalHistoryList.innerHTML = "<div style='color:var(--text-muted);font-size:12px;font-style:italic;'>No saved evaluations yet.</div>";
    return;
  }

  const pct = v => (v * 100).toFixed(1) + "%";
  const metricColor = v => v >= 0.7 ? "var(--success)" : v >= 0.4 ? "var(--warning)" : "var(--error)";
  const graphMap = Object.fromEntries(graphListCache.map(g => [g.graph_id, g]));

  evalHistoryList.innerHTML = `
    <div style="border:1px solid var(--border);border-radius:6px;overflow:hidden;">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 60px 60px 60px 52px 60px 60px 60px 60px 60px 48px 60px 24px;gap:8px;padding:5px 10px;background:var(--bg-lighter);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-muted);">
        <span>Graf</span><span>Prompt</span><span>Model</span><span>Sędzia</span><span>Prec.</span><span>Recall</span><span>F1</span><span>Hall.</span><span>Connect.</span><span>T-Prec.</span><span>T-Recall</span><span>T-F1</span><span>Unmatch.</span><span>Missing</span><span>GED</span><span></span>
      </div>
      ${items.map(e => {
        const g = graphMap[e.graph_id];
        const graphLabel = g ? (g.title || `#${e.graph_id}`) : `#${e.graph_id}`;
        const extractModel = g?.model ? g.model.replace(/^local:/, "").split("/").pop() : "—";
        const judgeModel = e.eval_model ? e.eval_model.replace(/^local:/, "").split("/").pop() : "—";
        const rateColor = v => v <= 0.3 ? "var(--success)" : v <= 0.6 ? "var(--warning)" : "var(--error)";
        const tF1Cell = e.t_f1 != null
          ? `<span style="font-weight:600;color:${metricColor(e.t_f1)};">${pct(e.t_f1)}</span>`
          : `<span style="color:var(--text-muted);">—</span>`;
        const tPrecCell = e.t_precision != null
          ? `<span style="font-weight:600;color:${metricColor(e.t_precision)};">${pct(e.t_precision)}</span>`
          : `<span style="color:var(--text-muted);">—</span>`;
        const tRecallCell = e.t_recall != null
          ? `<span style="font-weight:600;color:${metricColor(e.t_recall)};">${pct(e.t_recall)}</span>`
          : `<span style="color:var(--text-muted);">—</span>`;
        const hallCell = e.hallucination_rate != null
          ? `<span style="font-weight:600;color:${rateColor(e.hallucination_rate)};">${pct(e.hallucination_rate)}</span>`
          : `<span style="color:var(--text-muted);">—</span>`;
        const missingCell = e.omission_rate != null
          ? `<span style="font-weight:600;color:${rateColor(e.omission_rate)};">${pct(e.omission_rate)}</span>`
          : `<span style="color:var(--text-muted);">—</span>`;
        const gedCell = e.ged != null
          ? `<span style="font-weight:600;color:var(--text);">${e.ged}</span>`
          : `<span style="color:var(--text-muted);">—</span>`;
        const total = e.supported_count + e.unsupported_count;
        const hallucCell = `<span style="font-weight:600;color:${e.unsupported_count === 0 ? "var(--success)" : e.unsupported_count / total <= 0.3 ? "var(--warning)" : "var(--error)"};">${e.unsupported_count}/${total}</span>`;
        const connCell = e.connectivity_score != null
          ? `<span style="font-weight:600;color:${metricColor(e.connectivity_score)};">${pct(e.connectivity_score)}</span>`
          : `<span style="color:var(--text-muted);">—</span>`;
        return `<div class="eval-history-row" data-id="${e.id}" data-graph="${graphLabel}" data-prompt="${e.prompt_key}" style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 60px 60px 60px 52px 60px 60px 60px 60px 60px 48px 60px 24px;gap:8px;align-items:center;padding:6px 10px;border-top:1px solid var(--border);cursor:pointer;font-size:12px;transition:background 0.1s;">
          <span style="color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${graphLabel}</span>
          <span style="color:var(--text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${e.prompt_key}</span>
          <span style="color:var(--text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${extractModel}</span>
          <span style="color:var(--text-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${judgeModel}</span>
          <span style="font-weight:600;color:${metricColor(e.precision)};">${pct(e.precision)}</span>
          <span style="font-weight:600;color:${metricColor(e.recall)};">${pct(e.recall)}</span>
          <span style="font-weight:600;color:${metricColor(e.f1)};">${pct(e.f1)}</span>
          ${hallucCell}
          ${connCell}
          ${tPrecCell}
          ${tRecallCell}
          ${tF1Cell}
          ${hallCell}
          ${missingCell}
          ${gedCell}
          <span class="eval-history-delete" data-id="${e.id}" style="color:var(--text-muted);cursor:pointer;text-align:center;border-radius:3px;padding:1px 3px;font-size:12px;">✕</span>
        </div>`;
      }).join("")}
    </div>`;

  evalHistoryList.querySelectorAll(".eval-history-row").forEach(row => {
    row.addEventListener("mouseenter", () => row.style.background = "var(--bg-lighter)");
    row.addEventListener("mouseleave", () => row.style.background = "");
    row.addEventListener("click", async (e) => {
      if (e.target.classList.contains("eval-history-delete")) return;
      const id = parseInt(row.dataset.id);
      evalDetailSubtitle.textContent = `${row.dataset.graph} · ${row.dataset.prompt}`;
      evalDetailContent.innerHTML = "<div style='color:var(--text-muted);font-size:13px;'>Loading...</div>";
      evalDetailModal.classList.remove("hidden");
      const res = await fetch(`${API_BASE_URL}/evaluations/${id}`);
      const data = await res.json();
      evalDetailContent.innerHTML = buildEvalResultHtml(data);
    });
  });

  evalHistoryList.querySelectorAll(".eval-history-delete").forEach(btn => {
    btn.addEventListener("mouseenter", () => { btn.style.color = "var(--error)"; btn.style.background = "var(--error-bg)"; });
    btn.addEventListener("mouseleave", () => { btn.style.color = "var(--text-muted)"; btn.style.background = ""; });
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await fetch(`${API_BASE_URL}/evaluations/${parseInt(btn.dataset.id)}`, { method: "DELETE" });
      await loadEvalHistory();
    });
  });
}

async function openEvalModal() {
  evalResults.innerHTML = "";
  evalModal.classList.remove("hidden");

  const graphsRes = await fetch(`${API_BASE_URL}/graphs/all`);
  const allGraphs = (await graphsRes.json()) || [];

  graphListCache = allGraphs
    .filter(g => g.relation_count > 0 && g.article_id && g.prompt_key)
    .sort((a, b) => (b.position ?? 0) - (a.position ?? 0));

  const selGraph = document.getElementById("eval-graph-a");
  selGraph.innerHTML = "";

  if (graphListCache.length === 0) {
    const opt = document.createElement("option");
    opt.disabled = true;
    opt.textContent = "No graphs with linked article available";
    selGraph.appendChild(opt);
  } else {
    graphListCache.forEach(g => {
      const opt = document.createElement("option");
      opt.value = g.graph_id;
      const modelLabel = g.model ? g.model.replace(/^local:/, "").split("/").pop() : "—";
      opt.textContent = `[${g.position ?? "—"}] ${g.title ?? "—"} · ${modelLabel}`;
      selGraph.appendChild(opt);
    });
  }

  const selRefGraph = document.getElementById("eval-ref-graph");
  selRefGraph.innerHTML = "";
  const noneOpt = document.createElement("option");
  noneOpt.value = "";
  noneOpt.textContent = "— none —";
  selRefGraph.appendChild(noneOpt);
  allGraphs
    .filter(g => g.relation_count > 0)
    .sort((a, b) => (b.position ?? 0) - (a.position ?? 0))
    .forEach(g => {
      const opt = document.createElement("option");
      opt.value = g.graph_id;
      const modelLabel = g.model ? g.model.replace(/^local:/, "").split("/").pop() : "—";
      opt.textContent = `[${g.position ?? "—"}] ${g.title ?? "—"} · ${modelLabel}`;
      selRefGraph.appendChild(opt);
    });

  const selEvalModel = document.getElementById("eval-model");
  selEvalModel.innerHTML = document.getElementById("model-select").innerHTML;

  await loadEvalHistory();
}

compareBtn.addEventListener("click", openEvalModal);

evalCloseBtn.addEventListener("click", () => evalModal.classList.add("hidden"));
evalModal.addEventListener("click", (e) => { if (e.target === evalModal) evalModal.classList.add("hidden"); });

evalDetailClose.addEventListener("click", () => evalDetailModal.classList.add("hidden"));
evalDetailModal.addEventListener("click", (e) => { if (e.target === evalDetailModal) evalDetailModal.classList.add("hidden"); });

evalRunBtn.addEventListener("click", async () => {
  const graphId = parseInt(document.getElementById("eval-graph-a").value);
  const evalModel = document.getElementById("eval-model").value;
  const refVal = document.getElementById("eval-ref-graph").value;
  const referenceGraphId = refVal ? parseInt(refVal) : null;

  if (!graphId) { evalResults.innerHTML = "<div style='color:var(--error);font-size:13px;'>Select a graph.</div>"; return; }

  evalRunBtn.disabled = true;
  evalRunBtn.textContent = "Running...";
  evalResults.innerHTML = "<div style='color:var(--text-muted);font-size:13px;'>Evaluating graph...</div>";

  try {
    const res = await fetch(`${API_BASE_URL}/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ graph_id: graphId, model: evalModel, reference_graph_id: referenceGraphId }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    evalResults.innerHTML = buildEvalResultHtml(data);
    await loadEvalHistory();
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
