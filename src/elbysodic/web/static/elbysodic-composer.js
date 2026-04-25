(function () {
  const linkPattern = /\[([^\]\n]+)\]\(([^)\s]+)\)/g;

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#x27;");
  }

  function safeHref(value) {
    if (value.startsWith("/") || value.startsWith("#")) {
      return value;
    }
    try {
      const parsed = new URL(value, window.location.origin);
      if (["http:", "https:", "mailto:"].includes(parsed.protocol)) {
        return value;
      }
    } catch (_error) {
      return null;
    }
    return null;
  }

  function renderEmphasis(value) {
    return value
      .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
  }

  function renderInline(value) {
    let rendered = "";
    let lastEnd = 0;
    for (const match of value.matchAll(linkPattern)) {
      rendered += renderEmphasis(escapeHtml(value.slice(lastEnd, match.index)));
      const href = safeHref(match[2]);
      if (href) {
        rendered += `<a class="chirpui-link" href="${escapeHtml(href)}">${renderEmphasis(
          escapeHtml(match[1]),
        )}</a>`;
      } else {
        rendered += renderEmphasis(escapeHtml(match[0]));
      }
      lastEnd = match.index + match[0].length;
    }
    rendered += renderEmphasis(escapeHtml(value.slice(lastEnd)));
    return rendered;
  }

  function stripQuoteMarker(value) {
    let stripped = value.trimStart().slice(1);
    if (stripped.startsWith(" ")) {
      stripped = stripped.slice(1);
    }
    return stripped;
  }

  function paragraphs(lines) {
    const chunks = [[]];
    for (const line of lines) {
      if (line.trim()) {
        chunks[chunks.length - 1].push(line);
      } else if (chunks[chunks.length - 1].length > 0) {
        chunks.push([]);
      }
    }
    return chunks
      .filter((chunk) => chunk.length > 0)
      .map((chunk) => `<p>${chunk.map(renderInline).join("<br>")}</p>`)
      .join("");
  }

  function renderPostBody(value) {
    const lines = String(value).replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
    const blocks = [];
    let index = 0;
    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) {
        index += 1;
      } else if (line.trimStart().startsWith(">")) {
        const quoteLines = [];
        while (index < lines.length && lines[index].trimStart().startsWith(">")) {
          quoteLines.push(stripQuoteMarker(lines[index]));
          index += 1;
        }
        blocks.push(`<blockquote>${paragraphs(quoteLines)}</blockquote>`);
      } else {
        const paragraphLines = [];
        while (
          index < lines.length &&
          lines[index].trim() &&
          !lines[index].trimStart().startsWith(">")
        ) {
          paragraphLines.push(lines[index].trim());
          index += 1;
        }
        blocks.push(paragraphs(paragraphLines));
      }
    }
    return blocks.join("");
  }

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
      draftState: "",
      selectedCharacterId: String(config.selectedCharacterId || ""),
      title: config.initialTitle || "",
      viewMode: "write",

      get previewMode() {
        return this.viewMode === "preview";
      },

      init() {
        if (this.loadDraft()) {
          this.draftState = "restored";
        }
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
        this.draftState = "";
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
          this.draftState = "";
          return false;
        }
        try {
          const draft = JSON.parse(saved);
          this.body = draft.body || this.body;
          this.title = draft.title || this.title;
          this.draftState = "restored";
          return true;
        } catch (_error) {
          window.localStorage.removeItem(this.storageKey());
          return false;
        }
      },

      draftStatusText() {
        if (this.draftState === "restored") {
          return "Draft restored.";
        }
        if (this.draftState === "saved") {
          return "Draft saved.";
        }
        return "";
      },

      renderPreview() {
        return renderPostBody(this.body);
      },

      saveDraft() {
        if (!this.body.trim() && !this.title.trim()) {
          window.localStorage.removeItem(this.storageKey());
          this.draftState = "";
          return;
        }
        window.localStorage.setItem(this.storageKey(), this.draftPayload());
        this.draftState = "saved";
      },

      storageKey() {
        return `elbysodic:draft:${this.config.draftKey}:${this.selectedCharacterId}`;
      },
    };
  });
})();
