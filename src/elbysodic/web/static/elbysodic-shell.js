(function () {
  const COOKIE_NAME = "elbysodic_sidebar_hidden";
  const LEGACY_STORAGE_KEYS = ["chirpui-sidebar-collapsed", "elbysodic:sidebar-collapsed"];
  const HIDDEN_CLASS = "elbysodic-app-shell--sidebar-hidden";
  const YEAR_SECONDS = 60 * 60 * 24 * 365;

  function readCookiePreference() {
    const match = document.cookie.match(new RegExp(`(^|; )${COOKIE_NAME}=([^;]*)`));
    if (!match) {
      return null;
    }
    return decodeURIComponent(match[2]) === "true";
  }

  function readLegacyPreference() {
    try {
      for (const key of LEGACY_STORAGE_KEYS) {
        const value = window.localStorage.getItem(key);
        if (value !== null) {
          return value === "true";
        }
      }
    } catch (_error) {
      // Legacy migration is optional; cookie persistence is the source of truth.
    }
    return null;
  }

  function clearLegacyPreference() {
    try {
      for (const key of LEGACY_STORAGE_KEYS) {
        window.localStorage.removeItem(key);
      }
    } catch (_error) {
      // Best-effort cleanup only.
    }
  }

  function writeCookiePreference(hidden) {
    const secure = window.location.protocol === "https:" ? "; Secure" : "";
    document.cookie = `${COOKIE_NAME}=${hidden ? "true" : "false"}; Max-Age=${YEAR_SECONDS}; Path=/; SameSite=Lax${secure}`;
  }

  function readHiddenPreference() {
    const cookieValue = readCookiePreference();
    if (cookieValue !== null) {
      return cookieValue;
    }

    const legacyValue = readLegacyPreference();
    if (legacyValue !== null) {
      writeCookiePreference(legacyValue);
      clearLegacyPreference();
      return legacyValue;
    }
    return false;
  }

  function setSidebarState(shell, button, hidden) {
    document.documentElement.classList.toggle(HIDDEN_CLASS, hidden);
    shell.classList.toggle(HIDDEN_CLASS, hidden);
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupSidebarToggle);
  } else {
    setupSidebarToggle();
  }
  document.body.addEventListener("htmx:afterSettle", setupSidebarToggle);
})();
