(function () {
  const region = document.getElementById("brief-region");
  const slowMsg = document.getElementById("brief-slow-msg");
  const copyBtn = document.getElementById("copy-brief");
  const profileForm = document.getElementById("client-profile");
  const assetLimitMsg = document.getElementById("asset-limit-msg");

  function selectedAssets() {
    if (!profileForm) return [];
    return Array.from(
      profileForm.querySelectorAll('input[name="asset_classes"]:checked')
    );
  }

  function syncAssetLimit() {
    if (!profileForm) return true;
    const checked = selectedAssets();
    const over = checked.length > 2;
    if (assetLimitMsg) assetLimitMsg.hidden = !over;
    const boxes = profileForm.querySelectorAll('input[name="asset_classes"]');
    boxes.forEach(function (box) {
      if (!box.checked) box.disabled = checked.length >= 2;
    });
    const submit = profileForm.querySelector('button[type="submit"]');
    if (submit) submit.disabled = over;
    return !over;
  }

  if (profileForm) {
    profileForm.addEventListener("change", function (event) {
      if (event.target && event.target.name === "asset_classes") {
        syncAssetLimit();
      }
    });
    profileForm.addEventListener("submit", function (event) {
      if (!syncAssetLimit()) {
        event.preventDefault();
        return false;
      }
    });
    syncAssetLimit();
  }

  if (region && slowMsg) {
    let timer = null;
    const onBefore = function () {
      slowMsg.hidden = true;
      timer = window.setTimeout(function () {
        slowMsg.hidden = false;
      }, 15000);
    };
    const onAfter = function () {
      if (timer) {
        window.clearTimeout(timer);
        timer = null;
      }
      slowMsg.hidden = true;
      if (copyBtn) {
        copyBtn.hidden = false;
      }
    };
    region.addEventListener("htmx:beforeRequest", onBefore);
    region.addEventListener("htmx:afterRequest", onAfter);
    if (profileForm) {
      profileForm.addEventListener("htmx:beforeRequest", onBefore);
      profileForm.addEventListener("htmx:afterRequest", onAfter);
    }
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
