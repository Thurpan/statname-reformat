const inputBox = document.getElementById("inputBox");
const outputBox = document.getElementById("outputBox");
const formatBtn = document.getElementById("formatBtn");
const clearBtn = document.getElementById("clearBtn");
const statusEl = document.getElementById("status");

async function copyToClipboard(text) {
  try {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    statusEl.textContent = "Copied to clipboard.";
    setTimeout(() => (statusEl.textContent = ""), 1500);
  } catch (e) {
    // Clipboard may fail on some setups; don't block UI
    statusEl.textContent = "Copied (fallback may be needed).";
    setTimeout(() => (statusEl.textContent = ""), 1500);
  }
}

async function formatSummary() {
  const raw = inputBox.value || "";
  const body = JSON.stringify({ text: raw });

  const res = await fetch("/format", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  if (!res.ok) {
    outputBox.value = "";
    statusEl.textContent = "Error: could not format.";
    return;
  }

  const { output } = await res.json();
  outputBox.value = output || "";
  // Auto-copy to clipboard
  await copyToClipboard(outputBox.value);
}

formatBtn.addEventListener("click", formatSummary);

clearBtn.addEventListener("click", () => {
  inputBox.value = "";
  outputBox.value = "";
  statusEl.textContent = "";
  inputBox.focus();
});

// Support Ctrl+Enter / Cmd+Enter to format
inputBox.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    formatSummary();
  }
});
