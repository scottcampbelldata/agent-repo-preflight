// Progressive enhancement for the agent-repo-preflight web UI.
(function () {
  "use strict";

  // 1) Scan form: show a "scanning…" overlay on submit so the page never looks frozen
  //    while the synchronous scan runs server-side.
  const form = document.querySelector(".scan-form");
  const overlay = document.getElementById("scan-overlay");
  if (form && overlay) {
    form.addEventListener("submit", function () {
      const input = form.querySelector('input[name="target"]');
      const target = input ? input.value.trim() : "";
      const label = overlay.querySelector(".scan-overlay-target");
      if (label && target) label.textContent = target;
      overlay.hidden = false;
    });
  }

  // 2) Report page: copy-permalink button.
  const copyBtn = document.getElementById("copy-link");
  if (copyBtn) {
    copyBtn.addEventListener("click", async function () {
      try {
        await navigator.clipboard.writeText(window.location.href);
        const old = copyBtn.textContent;
        copyBtn.textContent = "Copied!";
        setTimeout(() => (copyBtn.textContent = old), 1500);
      } catch (e) {
        /* clipboard unavailable; ignore */
      }
    });
  }

  // 3) Report page: severity filter buttons toggle finding visibility.
  const filters = document.querySelectorAll("[data-filter]");
  const findings = document.querySelectorAll(".finding[data-severity]");
  if (filters.length && findings.length) {
    filters.forEach(function (btn) {
      btn.addEventListener("click", function () {
        const sev = btn.getAttribute("data-filter");
        filters.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        findings.forEach(function (f) {
          f.hidden = sev !== "all" && f.getAttribute("data-severity") !== sev;
        });
      });
    });
  }
})();
