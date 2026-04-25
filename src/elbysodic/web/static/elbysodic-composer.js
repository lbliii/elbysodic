(function () {
  function register(factory) {
    if (window._chirpAlpineData) {
      window._chirpAlpineData("elbysodicComposer", factory);
      return;
    }
    document.addEventListener("alpine:init", function () {
      Alpine.data("elbysodicComposer", factory);
    });
  }

  register(function (configId) {
    const configElement = document.getElementById(configId);
    const config = configElement ? JSON.parse(configElement.textContent || "{}") : {};

    return {
      body: config.initialBody || "",
      config: config,
      selectedCharacterId: String(config.selectedCharacterId || ""),
      title: config.initialTitle || "",
      viewMode: "write",

      get previewMode() {
        return this.viewMode === "preview";
      },

      init() {
        this.loadDraft();
        this.$watch("body", () => this.saveDraft());
        this.$watch("title", () => this.saveDraft());
        this.$watch("selectedCharacterId", () => this.loadDraft());
      },

      character() {
        const selected = this.config.characters.find(
          (character) => String(character.id) === String(this.selectedCharacterId),
        );
        return selected || this.config.characters[0] || {};
      },

      clearDraft() {
        window.localStorage.removeItem(this.storageKey());
      },

      draftPayload() {
        return JSON.stringify({
          body: this.body,
          title: this.title,
        });
      },

      hasPreview() {
        return this.body.trim().length > 0;
      },

      loadDraft() {
        const saved = window.localStorage.getItem(this.storageKey());
        if (!saved) {
          return;
        }
        try {
          const draft = JSON.parse(saved);
          this.body = draft.body || this.body;
          this.title = draft.title || this.title;
        } catch (_error) {
          window.localStorage.removeItem(this.storageKey());
        }
      },

      saveDraft() {
        if (!this.body.trim() && !this.title.trim()) {
          window.localStorage.removeItem(this.storageKey());
          return;
        }
        window.localStorage.setItem(this.storageKey(), this.draftPayload());
      },

      storageKey() {
        return `elbysodic:draft:${this.config.draftKey}:${this.selectedCharacterId}`;
      },
    };
  });
})();
