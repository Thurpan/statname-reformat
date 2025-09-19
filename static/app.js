const inputBox = document.getElementById("inputBox");
const outputBox = document.getElementById("outputBox");
const formatBtn = document.getElementById("formatBtn");
const pasteBtn = document.getElementById("pasteBtn");
const clearBtn = document.getElementById("clearBtn");
const copyBtn = document.getElementById("copyBtn");
const statusEl = document.getElementById("status");

function setStatus(msg, ms = 1500) {
  if (!statusEl) return;
  statusEl.textContent = msg || "";
  if (msg) setTimeout(() => (statusEl.textContent = ""), ms);
}

async function copyToClipboard(text) {
  try {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setStatus("Copied to clipboard.");
  } catch (err) {
    console.error("copy failed:", err);
    setStatus("Copy failed (clipboard permission?)");
  }
}

async function formatSummary() {
  const raw = inputBox.value || "";
  const res = await fetch("/format", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: raw }),
  });

  if (!res.ok) {
    outputBox.value = "";
    setStatus("Error: could not format.");
    return;
  }

  const { output } = await res.json();
  outputBox.value = output || "";
  await copyToClipboard(outputBox.value);
}

/* --------- Paste-and-Format (this is the key bit) --------- */
async function pasteAndFormat() {
  try {
    // Some browsers require an explicit permission check; ignore failures and try readText anyway.
    if (navigator.permissions && navigator.permissions.query) {
      try {
        // status can be 'granted' | 'denied' | 'prompt' — any of these may still allow readText on user gesture
        await navigator.permissions.query({ name: "clipboard-read" });
      } catch (_) {
        // ignore; not supported in all browsers
      }
    }

    const txt = await navigator.clipboard.readText(); // requires a user gesture (the click)
    if (!txt) {
      setStatus("Clipboard is empty.");
      return;
    }

    // (1) replace current input
    inputBox.value = txt;

    // (2) perform the same action as clicking Format
    await formatSummary();
  } catch (err) {
    console.error("paste failed:", err);
    // Friendly fallback: inform user how to enable or do manual paste
    setStatus("Paste blocked. Click input and press Ctrl+V (then click Format).");
    // Optionally focus input so Ctrl+V is easy
    inputBox.focus();
  }
}
/* ----------------------------------------------------------- */

// Wire up events (make sure this runs after the DOM is loaded)
formatBtn?.addEventListener("click", formatSummary);
pasteBtn?.addEventListener("click", pasteAndFormat);
clearBtn?.addEventListener("click", () => {
  inputBox.value = "";
  outputBox.value = "";
  setStatus("");
  inputBox.focus();
});
copyBtn?.addEventListener("click", () => copyToClipboard(outputBox.value));

// Shortcut: Ctrl/Cmd+Enter to format
inputBox.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    formatSummary();
  }
});
