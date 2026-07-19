(function () {
  const region = document.getElementById("brief-region");
  const slowMsg = document.getElementById("brief-slow-msg");
  const copyBtn = document.getElementById("copy-brief");
  const profileForm = document.getElementById("client-profile");
  const assetLimitMsg = document.getElementById("asset-limit-msg");
  const personaChips = Array.from(document.querySelectorAll(".persona-chip"));

  const personaPresets = {
    "conservative-hnw-sg": {
      tier: "High Net Worth",
      goal: "Capital Preservation",
      geography: "Singapore-centric",
      assets: ["Fixed Income / Bonds", "Equities (Singapore / Asia)"],
      portfolioMix: "20% equities / 60% bonds / 20% cash",
    },
    "income-affluent-asia": {
      tier: "Mass Affluent",
      goal: "Income Generation",
      geography: "Regional Asia",
      assets: [
        "Fixed Income / Bonds",
        "Real Assets (Property, REITs, Infrastructure)",
      ],
      portfolioMix: "30% equities / 50% bonds / 20% REITs",
    },
    "growth-hnw-global": {
      tier: "High Net Worth",
      goal: "Aggressive Growth",
      geography: "Global",
      assets: ["Global Equities", "Commodities"],
      portfolioMix: "75% global equities / 15% commodities / 10% cash",
    },
    "legacy-uhnw-sg": {
      tier: "Ultra High Net Worth",
      goal: "Legacy / Estate Planning",
      geography: "Singapore-centric",
      assets: [
        "Equities (Singapore / Asia)",
        "Real Assets (Property, REITs, Infrastructure)",
      ],
      portfolioMix: "40% Asia equities / 40% real assets / 20% bonds",
    },
  };

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

  function selectRadio(name, value) {
    const radios = profileForm.querySelectorAll('input[name="' + name + '"]');
    radios.forEach(function (radio) {
      radio.checked = radio.value === value;
    });
  }

  function applyPersonaPreset(key) {
    if (!profileForm || !personaPresets[key]) return;
    const preset = personaPresets[key];
    selectRadio("tier", preset.tier);
    selectRadio("goal", preset.goal);
    selectRadio("geography", preset.geography);

    const boxes = profileForm.querySelectorAll('input[name="asset_classes"]');
    boxes.forEach(function (box) {
      box.disabled = false;
      box.checked = preset.assets.includes(box.value);
    });
    const portfolioMix = profileForm.querySelector('input[name="portfolio_mix"]');
    if (portfolioMix) portfolioMix.value = preset.portfolioMix;
    syncAssetLimit();

    personaChips.forEach(function (chip) {
      const active = chip.dataset.persona === key;
      chip.classList.toggle("is-active", active);
      chip.setAttribute("aria-pressed", active ? "true" : "false");
    });
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

  personaChips.forEach(function (chip) {
    chip.setAttribute("aria-pressed", "false");
    chip.addEventListener("click", function () {
      applyPersonaPreset(chip.dataset.persona);
    });
  });

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

  document.addEventListener("click", async function (event) {
    const button = event.target.closest("#copy-email");
    if (!button) return;
    const draft = document.getElementById("client-email-draft");
    if (!draft) return;
    try {
      await navigator.clipboard.writeText(draft.innerText.trim());
      button.textContent = "Copied";
      window.setTimeout(function () {
        button.textContent = "Copy email";
      }, 1500);
    } catch (_) {
      button.textContent = "Copy failed";
    }
  });
})();
