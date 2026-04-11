const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const previewEl = document.getElementById("preview");
const titleEl = document.getElementById("title");
const sendBtn = document.getElementById("send-btn");
const clearGraphBtn = document.getElementById("clear-graph-btn");
const statusEl = document.getElementById("status");

let currentText = "";
let currentFileName = "";
let statusTimeout;

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

    titleEl.textContent = file.name.replace(/\.txt$/i, "").trim();

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
    const response = await fetch("/api/articles", {
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

    setStatus(
      'Article saved: ID = ' +
        data.article_id +
        ', title = "' +
        data.title +
        '"',
      "ok"
    );
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
    const response = await fetch("/api/graphs/clean", {
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
  } catch (err) {
    console.error(err);
    setStatus("Error deleting graph: " + err.message, "error");
  } finally {
    clearGraphBtn.disabled = false;
    clearGraphBtn.textContent = "Clear graph";
  }
});
