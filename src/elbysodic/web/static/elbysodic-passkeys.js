/* Elbysodic passkey UI — document-delegated sign-in and enrollment handlers.

   Uses the window.chirp.passkeys bridge injected by AppConfig(passkeys=True)
   for base64url <-> ArrayBuffer marshalling and navigator.credentials calls.
   An external 'self' script (not inline) so the handlers survive hx-boost
   shell swaps under a nonce-based CSP — same pattern as elbysodic-shell.js. */
(function () {
  "use strict";

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    var input = document.querySelector('input[name="_csrf_token"]');
    return input ? input.value : "";
  }

  function passkeysReady() {
    return !!(window.chirp && window.chirp.passkeys && window.PublicKeyCredential);
  }

  function syncPasskeyControls() {
    var ready = passkeysReady();
    var loginBtn = document.getElementById("passkey-login");
    var registerBtn = document.getElementById("passkey-register");
    var unsupported = document.getElementById("passkey-register-unsupported");
    if (loginBtn) loginBtn.hidden = !ready;
    if (registerBtn) registerBtn.hidden = !ready;
    if (unsupported) unsupported.hidden = ready;
  }

  function showError(id, message) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
  }

  function clearError(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.hidden = true;
  }

  async function ceremony(beginUrl, finishUrl, bridgeCall, extraFinishFields) {
    var csrf = csrfToken();
    var headers = csrf ? { "X-CSRF-Token": csrf } : {};
    var begin = await fetch(beginUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: headers,
    });
    if (!begin.ok) throw new Error("Could not start the passkey ceremony.");
    var options = await begin.json();
    var credential = await bridgeCall(options);
    var finish = await fetch(finishUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: Object.assign({ "Content-Type": "application/json" }, headers),
      body: JSON.stringify(Object.assign({}, credential, extraFinishFields || {})),
    });
    var result = await finish.json().catch(function () { return {}; });
    if (!finish.ok || !result.ok) {
      throw new Error(result.error || "Passkey ceremony failed.");
    }
    return result;
  }

  async function loginWithPasskey() {
    clearError("passkey-login-error");
    var loginBtn = document.getElementById("passkey-login");
    var loginForm = loginBtn && loginBtn.closest("form");
    var nextInput = loginForm
      ? loginForm.querySelector('input[name="next"]')
      : document.querySelector('form input[name="next"]');
    var nextUrl = (nextInput && nextInput.value) || "/";
    try {
      var result = await ceremony(
        "/login/passkeys/begin",
        "/login/passkeys/finish",
        function (options) { return window.chirp.passkeys.authenticate(options); },
        { next: nextUrl }
      );
      window.location = result.redirect || nextUrl;
    } catch (error) {
      if (error && error.passkeyReason === "cancelled") return;
      showError("passkey-login-error", (error && error.message) || "Passkey sign-in failed.");
    }
  }

  async function registerPasskey() {
    clearError("passkey-register-error");
    var labelInput = document.getElementById("passkey-label");
    var label = (labelInput && labelInput.value.trim()) || "";
    try {
      var result = await ceremony(
        "/identity/passkeys/begin",
        "/identity/passkeys/finish",
        function (options) { return window.chirp.passkeys.register(options); },
        { label: label }
      );
      window.location = result.redirect || "/identity";
    } catch (error) {
      if (error && error.passkeyReason === "cancelled") return;
      if (error && error.passkeyReason === "duplicate") {
        showError("passkey-register-error", "This device already has a passkey for the account.");
        return;
      }
      showError("passkey-register-error", (error && error.message) || "Passkey enrollment failed.");
    }
  }

  document.addEventListener("click", function (event) {
    var target = event.target;
    if (!target || typeof target.closest !== "function") return;
    if (!passkeysReady()) return;
    if (target.closest("#passkey-login")) {
      event.preventDefault();
      loginWithPasskey();
      return;
    }
    if (target.closest("#passkey-register")) {
      event.preventDefault();
      registerPasskey();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", syncPasskeyControls);
  } else {
    syncPasskeyControls();
  }
  document.addEventListener("htmx:afterSettle", syncPasskeyControls);
})();
