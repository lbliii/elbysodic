(function () {
  const COOKIE_NAME = "elbysodic_sidebar_hidden_v2";
  const HIDDEN_CLASS = "elbysodic-app-shell--sidebar-hidden";
  const YEAR_SECONDS = 60 * 60 * 24 * 365;

  function readCookiePreference() {
    const match = document.cookie.match(new RegExp(`(^|; )${COOKIE_NAME}=([^;]*)`));
    if (!match) {
      return null;
    }
    return decodeURIComponent(match[2]) === "true";
  }

  function clearLegacyPreference() {
    try {
      window.localStorage.removeItem("chirpui-sidebar-collapsed");
      window.localStorage.removeItem("elbysodic:sidebar-collapsed");
    } catch (_error) {
      // Best-effort cleanup only.
    }
  }

  function writeCookiePreference(hidden) {
    const secure = window.location.protocol === "https:" ? "; Secure" : "";
    document.cookie = `${COOKIE_NAME}=${hidden ? "true" : "false"}; Max-Age=${YEAR_SECONDS}; Path=/; SameSite=Lax${secure}`;
  }

  function setServerHiddenStyle(hidden) {
    const serverStyle = document.getElementById("elbysodic-sidebar-cookie-state");
    if (serverStyle) {
      serverStyle.disabled = !hidden;
    }
  }

  function readHiddenPreference() {
    const cookieValue = readCookiePreference();
    if (cookieValue !== null) {
      return cookieValue;
    }

    clearLegacyPreference();
    return false;
  }

  function setSidebarState(shell, button, hidden) {
    document.documentElement.classList.toggle(HIDDEN_CLASS, hidden);
    shell.classList.toggle(HIDDEN_CLASS, hidden);
    setServerHiddenStyle(hidden);
    button.setAttribute("aria-expanded", hidden ? "false" : "true");
    const label = hidden ? "Show navigation" : "Hide navigation";
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
  }

  function setupSidebarToggle() {
    const shell = document.querySelector(".chirpui-app-shell");
    const handle = document.querySelector("[data-elbysodic-sidebar-toggle]");
    if (!shell || !handle || handle.dataset.elbysodicSidebarReady === "true") {
      return;
    }

    function toggle() {
      const hidden = !shell.classList.contains(HIDDEN_CLASS);
      setSidebarState(shell, handle, hidden);
      writeCookiePreference(hidden);
      clearLegacyPreference();
    }

    handle.dataset.elbysodicSidebarReady = "true";
    setSidebarState(shell, handle, readHiddenPreference());
    handle.addEventListener("click", toggle);
    handle.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      toggle();
    });
  }

  function submitControls(scope) {
    return Array.from(
      scope.querySelectorAll(
        'button[type="submit"], input[type="submit"], button:not([type])',
      ),
    );
  }

  function setButtonLabel(button, label) {
    if (!button || !label || button.dataset.elbysodicSubmitLabelApplied === "true") {
      return;
    }
    button.dataset.elbysodicSubmitLabelApplied = "true";
    button.dataset.elbysodicSubmitOriginalLabel = button.textContent || "";
    button.textContent = label;
  }

  function setupSubmitGuards(root) {
    const forms = root.querySelectorAll('form[method="post"], form[method="POST"]');
    forms.forEach((form) => {
      if (form.dataset.elbysodicSubmitReady === "true") {
        return;
      }
      form.dataset.elbysodicSubmitReady = "true";
      form.addEventListener("submit", (event) => {
        if (form.dataset.elbysodicSubmitPending === "true") {
          event.preventDefault();
          return;
        }

        form.dataset.elbysodicSubmitPending = "true";
        form.setAttribute("aria-busy", "true");
        const group = form.closest("[data-elbysodic-submit-group]") || form;
        const submitter = event.submitter || form.querySelector('button[type="submit"]');
        setButtonLabel(submitter, form.dataset.elbysodicSubmitLabel);
        submitControls(group).forEach((control) => {
          control.disabled = true;
          control.setAttribute("aria-disabled", "true");
        });
      });
    });
  }

  function resetSubmitGuard(form) {
    if (!form || form.dataset.elbysodicSubmitPending !== "true") {
      return;
    }
    form.dataset.elbysodicSubmitPending = "false";
    form.removeAttribute("aria-busy");
    const group = form.closest("[data-elbysodic-submit-group]") || form;
    submitControls(group).forEach((control) => {
      control.disabled = false;
      control.removeAttribute("aria-disabled");
    });
    const labelled = group.querySelectorAll("[data-elbysodic-submit-label-applied='true']");
    labelled.forEach((control) => {
      control.textContent = control.dataset.elbysodicSubmitOriginalLabel || control.textContent;
      delete control.dataset.elbysodicSubmitLabelApplied;
      delete control.dataset.elbysodicSubmitOriginalLabel;
    });
  }

  function setupEnhancements() {
    setupSidebarToggle();
    setupSubmitGuards(document);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupEnhancements);
  } else {
    setupEnhancements();
  }
  document.body.addEventListener("htmx:afterSettle", () => setupEnhancements());
  document.body.addEventListener("htmx:responseError", (event) => {
    resetSubmitGuard(event.target && event.target.closest ? event.target.closest("form") : null);
  });
  window.addEventListener("pageshow", () => {
    document
      .querySelectorAll("form[data-elbysodic-submit-pending='true']")
      .forEach((form) => resetSubmitGuard(form));
  });
})();
