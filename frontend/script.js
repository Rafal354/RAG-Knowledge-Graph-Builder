const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const fileNameEl = document.getElementById("file-name");
const previewEl = document.getElementById("preview");
const sendBtn = document.getElementById("send-btn");
const statusEl = document.getElementById("status");

let currentText = "";
let currentFileName = "";

// na start blokujemy przycisk
sendBtn.disabled = true;

function resetStatus() {
  statusEl.textContent = "";
  statusEl.className = "";
}

function handleFile(file) {
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".txt")) {
    statusEl.textContent = "Only .txt files are handled";
    statusEl.className = "error";
    return;
  }

  resetStatus();

  const reader = new FileReader();
  reader.onload = (e) => {
    currentText = e.target.result || "";
    currentFileName = file.name;

    fileNameEl.textContent = "Chosen file: " + file.name;

    previewEl.textContent =
      currentText.slice(0, 1000) +
      (currentText.length > 1000 ? "…" : "");

    // odblokuj przycisk jeśli jest content
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
    statusEl.textContent = "No file selected";
    statusEl.className = "error";
    return;
  }

  const title = currentFileName.replace(/\.txt$/i, "").trim();

  if (!currentText.trim()) {
    statusEl.textContent = "Lack of content, file empty?";
    statusEl.className = "error";
    return;
  }

  sendBtn.disabled = true;
  sendBtn.textContent = "Processing request...";

  try {
    const response = await fetch("http://127.0.0.1:8000/articles", {
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

    statusEl.textContent =
      'Article saved: ID = ' +
      data.article_id +
      ', title = "' +
      data.title +
      '"';
    statusEl.className = "ok";
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Error processing request: " + err.message;
    statusEl.className = "error";
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Send request to the service";
  }
});