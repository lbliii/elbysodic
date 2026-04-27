(function () {
  const linkPattern = /\[([^\]\n]+)\]\(([^)\s]+)\)/g;
  const mentionPattern = /(?<![\w-])@([A-Za-z0-9][\w-]*)/g;

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

  function renderMentions(value, mentions) {
    let rendered = "";
    let lastEnd = 0;
    for (const match of value.matchAll(mentionPattern)) {
      rendered += renderEmphasis(escapeHtml(value.slice(lastEnd, match.index)));
      const mention = mentions.get(match[1].toLowerCase());
      if (mention) {
        rendered += `<a class="elbysodic-mention-link" data-mention-kind="${escapeHtml(
          mention.kind,
        )}" href="${escapeHtml(mention.href)}" title="${escapeHtml(mention.label)}">${escapeHtml(
          mention.tag,
        )}</a>`;
      } else {
        rendered += renderEmphasis(escapeHtml(match[0]));
      }
      lastEnd = match.index + match[0].length;
    }
    rendered += renderEmphasis(escapeHtml(value.slice(lastEnd)));
    return rendered;
  }

  function renderInline(value, mentions) {
    let rendered = "";
    let lastEnd = 0;
    for (const match of value.matchAll(linkPattern)) {
      rendered += renderMentions(value.slice(lastEnd, match.index), mentions);
      const href = safeHref(match[2]);
      if (href) {
        rendered += `<a class="chirpui-link" href="${escapeHtml(href)}">${renderEmphasis(
          escapeHtml(match[1]),
        )}</a>`;
      } else {
        rendered += renderMentions(match[0], mentions);
      }
      lastEnd = match.index + match[0].length;
    }
    rendered += renderMentions(value.slice(lastEnd), mentions);
    return rendered;
  }

  function stripQuoteMarker(value) {
    let stripped = value.trimStart().slice(1);
    if (stripped.startsWith(" ")) {
      stripped = stripped.slice(1);
    }
    return stripped;
  }

  function paragraphs(lines, mentions) {
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
      .map((chunk) => `<p>${chunk.map((line) => renderInline(line, mentions)).join("<br>")}</p>`)
      .join("");
  }

  function renderPostBody(value, mentions) {
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
        blocks.push(`<blockquote>${paragraphs(quoteLines, mentions)}</blockquote>`);
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
        blocks.push(paragraphs(paragraphLines, mentions));
      }
    }
    return blocks.join("");
  }

  function formatBody(value, start, end, kind) {
    const selected = value.slice(start, end);
    if (kind === "bold") {
      return wrapSelection(value, start, end, selected || "bold text", "**", "**");
    }
    if (kind === "italic") {
      return wrapSelection(value, start, end, selected || "italic text", "*", "*");
    }
    if (kind === "quote") {
      return quoteSelection(value, start, end, selected || "quoted text");
    }
    if (kind === "link") {
      return linkSelection(value, start, end, selected || "link text");
    }
    return {
      end: end,
      next: value,
      start: start,
    };
  }

  function wrapSelection(value, start, end, selected, prefix, suffix) {
    const insertion = `${prefix}${selected}${suffix}`;
    const innerStart = start + prefix.length;
    return {
      end: innerStart + selected.length,
      next: value.slice(0, start) + insertion + value.slice(end),
      start: innerStart,
    };
  }

  function quoteSelection(value, start, end, selected) {
    const insertion = selected
      .split("\n")
      .map((line) => `> ${line}`)
      .join("\n");
    return {
      end: start + insertion.length,
      next: value.slice(0, start) + insertion + value.slice(end),
      start: start,
    };
  }

  function linkSelection(value, start, end, selected) {
    const url = "https://";
    const insertion = `[${selected}](${url})`;
    const urlStart = start + selected.length + 3;
    return {
      end: urlStart + url.length,
      next: value.slice(0, start) + insertion + value.slice(end),
      start: urlStart,
    };
  }

  function register(name, factory) {
    if (window._chirpAlpineData) {
      window._chirpAlpineData(name, factory);
      return;
    }
    document.addEventListener("alpine:init", function () {
      Alpine.data(name, factory);
    });
  }

  function readConfig(configId) {
    const configElement = document.getElementById(configId);
    return configElement ? JSON.parse(configElement.textContent || "{}") : {};
  }

  function removeManagedClasses(element, prefixes) {
    if (!element) {
      return;
    }
    for (const className of Array.from(element.classList)) {
      if (prefixes.some((prefix) => className.startsWith(prefix))) {
        element.classList.remove(className);
      }
    }
  }

  register("elbysodicPostStylePreview", function (configId) {
    const config = readConfig(configId);
    const initial = config.initial || {};

    return {
      accentSource: initial.accentSource || "inherit",
      customAccent: initial.customAccent || "",
      inheritedAccentColor: config.inheritedAccentColor || "",
      inheritedAccentLabel: config.inheritedAccentLabel || "Inherit from community direction",
      name: initial.name || "",
      postAccentStyle: initial.postAccentStyle || "soft",
      postBorderStyle: initial.postBorderStyle || "hairline",
      postDensity: initial.postDensity || "calm",
      postProfileVariant: initial.postProfileVariant || "bio",
      postTitleStyle: initial.postTitleStyle || "standard",
      posterAlt: initial.posterAlt || "",
      posterUrl: initial.posterUrl || "",
      presets: config.presets || {},
      stylePreset: initial.stylePreset || "",
      summary: initial.summary || "",
      tagline: initial.tagline || "",
      writer: initial.writer || "",

      accentLabel() {
        if (this.accentSource === "custom" && this.customAccent.trim()) {
          return "Custom accent";
        }
        return this.inheritedAccentLabel;
      },

      applyPreset() {
        const preset = this.presets[this.stylePreset];
        if (!preset) {
          return;
        }
        this.postProfileVariant = preset.post_profile_variant || this.postProfileVariant;
        this.postAccentStyle = preset.post_accent_style || this.postAccentStyle;
        this.postBorderStyle = preset.post_border_style || this.postBorderStyle;
        this.postTitleStyle = preset.post_title_style || this.postTitleStyle;
        this.postDensity = preset.post_density || this.postDensity;
      },

      displayInitial() {
        return this.displayName().trim().slice(0, 1) || "?";
      },

      displayName() {
        return this.name.trim() || "New face";
      },

      displaySummary() {
        return this.summary.trim() || "A quick character note will live here.";
      },

      hasPoster() {
        return this.posterUrl.trim().length > 0;
      },

      previewAccent() {
        if (this.accentSource === "custom" && this.customAccent.trim()) {
          return this.customAccent.trim();
        }
        return this.inheritedAccentColor;
      },

      previewAlt() {
        return this.posterAlt.trim() || this.displayName();
      },

      previewBodyLead() {
        return `${this.displayName()} steps into the scene with just enough atmosphere to feel authored, while the prose column keeps its calm reading rhythm.`;
      },

      syncPreviewClasses(shell) {
        const accent = this.previewAccent();
        if (shell) {
          removeManagedClasses(shell, [
            "elbysodic-post-accent--",
            "elbysodic-post-border--",
            "elbysodic-post-title--",
            "elbysodic-post-density--",
          ]);
          shell.classList.add(
            `elbysodic-post-accent--${this.postAccentStyle || "soft"}`,
            `elbysodic-post-border--${this.postBorderStyle || "hairline"}`,
            `elbysodic-post-title--${this.postTitleStyle || "standard"}`,
            `elbysodic-post-density--${this.postDensity || "calm"}`,
          );
          if (accent) {
            shell.style.setProperty("--elbysodic-character-accent", accent);
          } else {
            shell.style.removeProperty("--elbysodic-character-accent");
          }
        }
        if (this.$refs.previewRail) {
          removeManagedClasses(this.$refs.previewRail, ["elbysodic-post-profile--"]);
          this.$refs.previewRail.classList.add(
            `elbysodic-post-profile--${this.postProfileVariant || "bio"}`,
          );
        }
        if (this.$refs.previewSwatch) {
          if (accent) {
            this.$refs.previewSwatch.style.setProperty("--elbysodic-accent-source-color", accent);
          } else {
            this.$refs.previewSwatch.style.removeProperty("--elbysodic-accent-source-color");
          }
        }
      },
    };
  });

  register("elbysodicMentionPicker", function (configId) {
    const config = readConfig(configId);

    return {
      config: config,
      highlightedIndex: 0,
      loading: false,
      open: false,
      query: "",
      results: [],
      selected: config.selected || [],

      selectedKey(item) {
        return `${item.kind}:${item.id}`;
      },

      selectedKeys() {
        return new Set(this.selected.map((item) => this.selectedKey(item)));
      },

      close() {
        this.open = false;
        this.highlightedIndex = 0;
      },

      chooseHighlighted() {
        if (!this.open || this.results.length === 0) {
          return;
        }
        this.select(this.results[this.highlightedIndex] || this.results[0]);
      },

      move(delta) {
        if (!this.open || this.results.length === 0) {
          return;
        }
        this.highlightedIndex =
          (this.highlightedIndex + delta + this.results.length) % this.results.length;
      },

      remove(item) {
        const key = this.selectedKey(item);
        this.selected = this.selected.filter((selectedItem) => this.selectedKey(selectedItem) !== key);
        this.$nextTick(() => this.$refs.search.focus());
      },

      select(item) {
        if (!this.selectedKeys().has(this.selectedKey(item))) {
          this.selected = [...this.selected, item];
        }
        this.query = "";
        this.results = [];
        this.close();
        this.$nextTick(() => this.$refs.search.focus());
      },

      async search() {
        const term = this.query.trim().replace(/^@+/, "");
        if (!term) {
          this.results = [];
          this.close();
          return;
        }
        this.loading = true;
        const params = new URLSearchParams({
          q: term,
          scope: this.config.scope || "all",
        });
        try {
          const response = await fetch(`${this.config.endpoint}?${params.toString()}`, {
            credentials: "same-origin",
          });
          if (!response.ok) {
            this.results = [];
            this.close();
            return;
          }
          const payload = await response.json();
          const selected = this.selectedKeys();
          this.results = (payload.items || []).filter(
            (item) => !selected.has(this.selectedKey(item)),
          );
          this.highlightedIndex = 0;
          this.open = this.results.length > 0;
        } finally {
          this.loading = false;
        }
      },
    };
  });

  register("elbysodicComposer", function (configId) {
    const config = readConfig(configId);

    return {
      body: config.initialBody || "",
      bodyMentionFieldId: "",
      bodyMentionHighlightedIndex: 0,
      bodyMentionOpen: false,
      bodyMentionQuery: "",
      bodyMentionResults: [],
      config: config,
      draftState: "",
      knownMentionables: {},
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

      applyFormat(kind, fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) {
          return;
        }
        const start = field.selectionStart || 0;
        const end = field.selectionEnd || start;
        const formatted = formatBody(this.body, start, end, kind);
        this.body = formatted.next;
        this.$nextTick(() => {
          field.focus();
          field.setSelectionRange(formatted.start, formatted.end);
          this.saveDraft();
        });
      },

      bodyMentionKeydown(event, fieldId) {
        if (!this.bodyMentionOpen) {
          return;
        }
        if (event.key === "ArrowDown") {
          event.preventDefault();
          this.moveBodyMention(1);
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          this.moveBodyMention(-1);
        } else if (event.key === "Enter") {
          event.preventDefault();
          this.chooseBodyMention(fieldId);
        } else if (event.key === "Escape") {
          event.preventDefault();
          this.closeBodyMention();
        }
      },

      chooseBodyMention(fieldId) {
        if (!this.bodyMentionOpen || this.bodyMentionResults.length === 0) {
          return;
        }
        this.insertBodyMention(
          this.bodyMentionResults[this.bodyMentionHighlightedIndex] || this.bodyMentionResults[0],
          fieldId,
        );
      },

      clearDraft() {
        window.localStorage.removeItem(this.storageKey());
        this.draftState = "";
      },

      closeBodyMention() {
        this.bodyMentionOpen = false;
        this.bodyMentionHighlightedIndex = 0;
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

      activeBodyMention(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) {
          return null;
        }
        const cursor = field.selectionStart || 0;
        const before = this.body.slice(0, cursor);
        const match = before.match(/(?:^|[^\w-])@([A-Za-z0-9][\w-]*)$/);
        if (!match) {
          return null;
        }
        return {
          end: cursor,
          query: match[1],
          start: cursor - match[1].length - 1,
        };
      },

      insertBodyMention(item, fieldId) {
        const active = this.activeBodyMention(fieldId);
        const field = document.getElementById(fieldId);
        if (!active || !field) {
          return;
        }
        this.rememberMention(item);
        const insertion = `${item.tag} `;
        this.body =
          this.body.slice(0, active.start) + insertion + this.body.slice(active.end);
        const nextCursor = active.start + insertion.length;
        this.closeBodyMention();
        this.$nextTick(() => {
          field.focus();
          field.setSelectionRange(nextCursor, nextCursor);
          this.saveDraft();
        });
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
        return renderPostBody(this.body, this.mentionMap());
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

      mentionKey(item) {
        return `${item.kind}:${item.id}`;
      },

      mentionMap() {
        const mentions = new Map();
        for (const item of Object.values(this.knownMentionables)) {
          mentions.set(String(item.handle).toLowerCase(), item);
        }
        return mentions;
      },

      moveBodyMention(delta) {
        if (!this.bodyMentionOpen || this.bodyMentionResults.length === 0) {
          return;
        }
        this.bodyMentionHighlightedIndex =
          (this.bodyMentionHighlightedIndex + delta + this.bodyMentionResults.length) %
          this.bodyMentionResults.length;
      },

      rememberMention(item) {
        this.knownMentionables = {
          ...this.knownMentionables,
          [this.mentionKey(item)]: item,
        };
      },

      rememberMentions(items) {
        const next = { ...this.knownMentionables };
        for (const item of items) {
          next[this.mentionKey(item)] = item;
        }
        this.knownMentionables = next;
      },

      async searchBodyMention(fieldId) {
        const active = this.activeBodyMention(fieldId);
        if (!active || !active.query) {
          this.bodyMentionResults = [];
          this.closeBodyMention();
          return;
        }
        this.bodyMentionFieldId = fieldId;
        this.bodyMentionQuery = active.query;
        const params = new URLSearchParams({
          q: active.query,
          scope: this.config.mentionScope || "all",
        });
        const response = await fetch(`${this.config.mentionEndpoint}?${params.toString()}`, {
          credentials: "same-origin",
        });
        if (!response.ok) {
          this.bodyMentionResults = [];
          this.closeBodyMention();
          return;
        }
        const payload = await response.json();
        this.bodyMentionResults = payload.items || [];
        this.rememberMentions(this.bodyMentionResults);
        this.bodyMentionHighlightedIndex = 0;
        this.bodyMentionOpen = this.bodyMentionResults.length > 0;
      },
    };
  });
})();

(function () {
  const STORAGE_KEY = "chirpui-sidebar-collapsed";
  const LEGACY_STORAGE_KEY = "elbysodic:sidebar-collapsed";
  const COLLAPSED_CLASS = "elbysodic-app-shell--sidebar-collapsed";
  const CHIRPUI_COLLAPSED_CLASS = "chirpui-app-shell--sidebar-collapsed";
  const CHIRPUI_COLLAPSIBLE_CLASS = "chirpui-app-shell--sidebar-collapsible";

  function readCollapsedPreference() {
    try {
      const value =
        window.localStorage.getItem(STORAGE_KEY) ??
        window.localStorage.getItem(LEGACY_STORAGE_KEY);
      return value === "true";
    } catch (_error) {
      return false;
    }
  }

  function writeCollapsedPreference(collapsed) {
    try {
      window.localStorage.setItem(STORAGE_KEY, collapsed ? "true" : "false");
    } catch (_error) {
      // Persistence is a convenience; the shell still works without storage.
    }
  }

  function setSidebarState(shell, button, collapsed) {
    shell.classList.toggle(COLLAPSED_CLASS, collapsed);
    shell.classList.toggle(CHIRPUI_COLLAPSED_CLASS, collapsed);
    shell.classList.add(CHIRPUI_COLLAPSIBLE_CLASS);
    button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    button.setAttribute(
      "aria-label",
      collapsed ? "Expand sidebar" : "Collapse sidebar",
    );
  }

  function setupSidebarToggle() {
    const shell = document.querySelector(".chirpui-app-shell");
    const handle = document.querySelector("[data-elbysodic-sidebar-toggle]");
    if (!shell || !handle || handle.dataset.elbysodicSidebarReady === "true") {
      return;
    }

    let dragging = false;
    let startX = 0;
    let lastX = 0;
    let startCollapsed = false;

    function toggle() {
      const collapsed = !shell.classList.contains(COLLAPSED_CLASS);
      setSidebarState(shell, handle, collapsed);
      writeCollapsedPreference(collapsed);
    }

    handle.dataset.elbysodicSidebarReady = "true";
    setSidebarState(shell, handle, readCollapsedPreference());
    handle.addEventListener("mousedown", (event) => {
      event.preventDefault();
      dragging = true;
      startX = event.clientX;
      lastX = event.clientX;
      startCollapsed = shell.classList.contains(COLLAPSED_CLASS);
      document.body.style.userSelect = "none";
    });
    handle.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      toggle();
    });
    window.addEventListener("mousemove", (event) => {
      if (!dragging) {
        return;
      }
      lastX = event.clientX;
    });
    window.addEventListener("mouseup", () => {
      if (!dragging) {
        return;
      }
      dragging = false;
      document.body.style.userSelect = "";
      const delta = lastX - startX;
      if (Math.abs(delta) < 5) {
        toggle();
        return;
      }
      if (delta < 0 && !startCollapsed) {
        setSidebarState(shell, handle, true);
        writeCollapsedPreference(true);
      } else if (delta > 0 && startCollapsed) {
        setSidebarState(shell, handle, false);
        writeCollapsedPreference(false);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupSidebarToggle);
  } else {
    setupSidebarToggle();
  }
  document.body.addEventListener("htmx:afterSettle", setupSidebarToggle);
})();
