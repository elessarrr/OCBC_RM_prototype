(function () {
  const region = document.getElementById("brief-region");
  const slowMsg = document.getElementById("brief-slow-msg");
  const copyBtn = document.getElementById("copy-brief");

  if (region && slowMsg) {
    let timer = null;
    region.addEventListener("htmx:beforeRequest", function () {
      slowMsg.hidden = true;
      timer = window.setTimeout(function () {
        slowMsg.hidden = false;
      }, 15000);
    });
    region.addEventListener("htmx:afterRequest", function () {
      if (timer) {
        window.clearTimeout(timer);
        timer = null;
      }
      slowMsg.hidden = true;
      if (copyBtn) {
        copyBtn.hidden = false;
      }
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", async function () {
      const textEl = document.getElementById("brief-text");
      if (!textEl) return;
      const text = textEl.innerText.trim();
      try {
        await navigator.clipboard.writeText(text);
        copyBtn.textContent = "Copied";
        window.setTimeout(function () {
          copyBtn.textContent = "Copy";
        }, 1500);
      } catch (_) {
        copyBtn.textContent = "Copy failed";
      }
    });
  }
})();
