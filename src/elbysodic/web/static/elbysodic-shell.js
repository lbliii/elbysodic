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

  function setToggleControlState(control, hidden) {
    control.setAttribute("aria-expanded", hidden ? "false" : "true");
    const label = hidden ? "Show navigation" : "Hide navigation";
    control.setAttribute("aria-label", label);
    control.setAttribute("title", label);
  }

  function setSidebarState(shell, controls, hidden) {
    document.documentElement.classList.toggle(HIDDEN_CLASS, hidden);
    shell.classList.toggle(HIDDEN_CLASS, hidden);
    setServerHiddenStyle(hidden);
    controls.forEach((control) => setToggleControlState(control, hidden));
  }

  function setupSidebarToggle() {
    const shell = document.querySelector(".chirpui-app-shell");
    const controls = Array.from(document.querySelectorAll("[data-elbysodic-sidebar-toggle]"));
    if (!shell || controls.length === 0) {
      return;
    }

    function toggle() {
      const hidden = !shell.classList.contains(HIDDEN_CLASS);
      setSidebarState(shell, controls, hidden);
      writeCookiePreference(hidden);
      clearLegacyPreference();
    }

    controls.forEach((control) => {
      if (control.dataset.elbysodicSidebarReady === "true") {
        return;
      }
      control.dataset.elbysodicSidebarReady = "true";
      control.addEventListener("click", toggle);
      control.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") {
          return;
        }
        event.preventDefault();
        toggle();
      });
    });
    setSidebarState(shell, controls, readHiddenPreference());
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

  function fieldValue(form, name) {
    const field = form.elements.namedItem(name);
    if (!field) {
      return "";
    }
    return String(field.value || "").trim();
  }

  function selectedText(form, name) {
    const field = form.elements.namedItem(name);
    if (!field || !field.options || field.selectedIndex < 0) {
      return fieldValue(form, name);
    }
    return String(field.options[field.selectedIndex].textContent || "").trim();
  }

  function setText(target, value) {
    if (!target) {
      return;
    }
    target.textContent = value;
  }

  function setBadgeText(target, value) {
    if (!target) {
      return;
    }
    const badge = target.querySelector("[class*='chirpui-badge']");
    setText(badge || target, value);
  }

  function tagEntries(source) {
    return source
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const parts = line.split("|").map((part) => part.trim());
        return {
          key: parts[1] || parts[0] || "",
          label: parts[2] || parts[1] || parts[0] || "",
        };
      })
      .filter((entry) => entry.key && entry.label);
  }

  function updateDiscoveryPreview(form) {
    const card = document.querySelector("[data-elbysodic-discovery-preview-card]");
    if (!card) {
      return;
    }

    const summary = card.querySelector("[data-elbysodic-preview-summary]");
    if (summary && !summary.dataset.elbysodicPreviewDefault) {
      summary.dataset.elbysodicPreviewDefault = summary.textContent.trim();
    }
    const fit = card.querySelector("[data-elbysodic-preview-fit]");
    const access = card.querySelector("[data-elbysodic-preview-access]");
    const pace = card.querySelector("[data-elbysodic-preview-pace]");
    const tags = document.querySelector("[data-elbysodic-preview-tags]");

    const catalogPitch = fieldValue(form, "catalog_pitch");
    setText(summary, catalogPitch || (summary ? summary.dataset.elbysodicPreviewDefault : ""));
    setBadgeText(access, selectedText(form, "access_model"));
    setBadgeText(pace, fieldValue(form, "activity_pace"));

    const fitLabels = [
      fieldValue(form, "premise_archetype") || "Premise-led realm",
      fieldValue(form, "lore_aperture"),
      fieldValue(form, "forum_adjunct"),
    ].filter(Boolean);
    setText(fit, fitLabels.join(" · "));

    if (tags) {
      const entries = tagEntries(fieldValue(form, "discovery_tags"));
      tags.hidden = entries.length === 0;
      tags.replaceChildren(
        ...entries.map((entry) => {
          const link = document.createElement("a");
          link.href = `/network?q=${encodeURIComponent(entry.key)}`;
          link.textContent = entry.label;
          return link;
        }),
      );
    }
  }

  function setupDiscoveryPreview(root) {
    const forms = root.querySelectorAll("[data-elbysodic-discovery-preview-form]");
    forms.forEach((form) => {
      if (form.dataset.elbysodicDiscoveryPreviewReady === "true") {
        return;
      }
      form.dataset.elbysodicDiscoveryPreviewReady = "true";
      updateDiscoveryPreview(form);
      form.addEventListener("input", () => updateDiscoveryPreview(form));
      form.addEventListener("change", () => updateDiscoveryPreview(form));
    });
  }

  function gatewayItems(list) {
    return Array.from(list.querySelectorAll("[data-elbysodic-gateway-curation-item]"));
  }

  function directEmptyState(list) {
    return Array.from(list.children).find((child) =>
      child.matches("[data-elbysodic-spotlight-empty]"),
    );
  }

  function updateSpotlightEmpty(list) {
    const empty = directEmptyState(list);
    if (!empty) {
      return;
    }
    empty.hidden = gatewayItems(list).length > 0;
  }

  function setSpotlightItemState(item, selected) {
    const input = item.querySelector("[data-elbysodic-gateway-curation-select]");
    if (input) {
      input.checked = selected;
    }
    item.classList.toggle("elbysodic-spotlight-item--selected", selected);
    item.classList.toggle("elbysodic-spotlight-item--available", !selected);
    item.draggable = selected;
  }

  function updateGatewayCurationPositions(list) {
    let selectedIndex = 0;
    gatewayItems(list).forEach((item, index) => {
      const position = (index + 1) * 10;
      const input = item.querySelector("[data-elbysodic-gateway-curation-position]");
      const rank = item.querySelector("[data-elbysodic-gateway-curation-rank]");
      const selected = item.querySelector("[data-elbysodic-gateway-curation-select]");
      if (input) {
        input.value = String(position);
      }
      if (rank) {
        if (selected && selected.checked) {
          selectedIndex += 1;
          rank.textContent = String(selectedIndex).padStart(2, "0");
        } else {
          rank.textContent = "";
        }
      }
    });
    const lane = list.closest(".elbysodic-spotlight-lane");
    const count = lane ? lane.querySelector("[data-elbysodic-spotlight-count]") : null;
    if (count) {
      count.textContent = String(selectedIndex);
    }
    updateSpotlightEmpty(list);
  }

  function moveGatewayCurationItem(item, direction) {
    const list = item.closest("[data-elbysodic-gateway-curation-list]");
    if (!list) {
      return;
    }
    if (direction < 0 && item.previousElementSibling) {
      list.insertBefore(item, item.previousElementSibling);
    }
    if (direction > 0 && item.nextElementSibling) {
      list.insertBefore(item.nextElementSibling, item);
    }
    updateGatewayCurationPositions(list);
    updateSpotlightComposer(list.closest("[data-elbysodic-spotlight-composer]"), true);
    item.focus({ preventScroll: true });
  }

  function gatewayCurationDropTarget(list, y) {
    return gatewayItems(list).find((item) => {
      if (item.getAttribute("aria-grabbed") === "true") {
        return false;
      }
      const box = item.getBoundingClientRect();
      return y < box.top + box.height / 2;
    });
  }

  function moveSpotlightItem(item, selected) {
    const composer = item.closest("[data-elbysodic-spotlight-composer]");
    const currentList = item.closest("[data-elbysodic-spotlight-list-for]");
    if (!composer || !currentList) {
      return;
    }
    const slotType = currentList.dataset.elbysodicSpotlightListFor;
    const selector = selected
      ? "[data-elbysodic-spotlight-selected-list]"
      : "[data-elbysodic-spotlight-library-list]";
    const targetList = composer.querySelector(
      `${selector}[data-elbysodic-spotlight-list-for="${slotType}"]`,
    );
    if (!targetList || targetList === currentList) {
      return;
    }
    targetList.appendChild(item);
    setSpotlightItemState(item, selected);
    updateSpotlightEmpty(currentList);
    updateSpotlightEmpty(targetList);
    const selectedList = composer.querySelector(
      `[data-elbysodic-spotlight-selected-list][data-elbysodic-spotlight-list-for="${slotType}"]`,
    );
    if (selectedList) {
      updateGatewayCurationPositions(selectedList);
    }
    updateSpotlightComposer(composer, true);
    item.focus({ preventScroll: true });
  }

  function updateSpotlightPreview(composer) {
    if (!composer) {
      return;
    }
    const list = composer.querySelector("[data-elbysodic-spotlight-preview-list]");
    const empty = composer.querySelector("[data-elbysodic-spotlight-preview-empty]");
    if (!list) {
      return;
    }
    const items = Array.from(
      composer.querySelectorAll(
        "[data-elbysodic-spotlight-selected-list] [data-elbysodic-spotlight-item]",
      ),
    );
    list.replaceChildren(
      ...items.slice(0, 6).map((item) => {
        const row = document.createElement("li");
        const type = document.createElement("span");
        const title = document.createElement("strong");
        type.textContent = item.dataset.elbysodicSpotlightType || "Spotlight";
        title.textContent = item.dataset.elbysodicSpotlightTitle || "Untitled";
        row.append(type, title);
        return row;
      }),
    );
    if (empty) {
      empty.hidden = items.length > 0;
    }
  }

  function updateSpotlightComposer(composer, dirty) {
    if (!composer) {
      return;
    }
    composer
      .querySelectorAll("[data-elbysodic-gateway-curation-list]")
      .forEach(updateGatewayCurationPositions);
    composer
      .querySelectorAll("[data-elbysodic-spotlight-library-list]")
      .forEach(updateSpotlightEmpty);
    updateSpotlightPreview(composer);
    if (dirty) {
      const label = composer.querySelector("[data-elbysodic-spotlight-dirty]");
      if (label) {
        label.textContent = "Unsaved spotlight changes";
        label.dataset.elbysodicDirty = "true";
      }
    }
  }

  function setupGatewayCuration(root) {
    const composers = root.querySelectorAll("[data-elbysodic-spotlight-composer]");
    composers.forEach((composer) => {
      if (composer.dataset.elbysodicSpotlightComposerReady === "true") {
        return;
      }
      composer.dataset.elbysodicSpotlightComposerReady = "true";
      composer.addEventListener("click", (event) => {
        const add = event.target.closest("[data-elbysodic-spotlight-add]");
        const remove = event.target.closest("[data-elbysodic-spotlight-remove]");
        if (!add && !remove) {
          return;
        }
        event.preventDefault();
        const item = event.target.closest("[data-elbysodic-spotlight-item]");
        if (item) {
          moveSpotlightItem(item, Boolean(add));
        }
      });
      updateSpotlightComposer(composer, false);
    });

    const lists = root.querySelectorAll("[data-elbysodic-gateway-curation-list]");
    lists.forEach((list) => {
      if (list.dataset.elbysodicGatewayCurationReady === "true") {
        return;
      }
      list.dataset.elbysodicGatewayCurationReady = "true";
      updateGatewayCurationPositions(list);

      list.addEventListener("click", (event) => {
        const up = event.target.closest("[data-elbysodic-gateway-curation-up]");
        const down = event.target.closest("[data-elbysodic-gateway-curation-down]");
        if (!up && !down) {
          return;
        }
        event.preventDefault();
        const item = event.target.closest("[data-elbysodic-gateway-curation-item]");
        if (item) {
          moveGatewayCurationItem(item, up ? -1 : 1);
        }
      });

      list.addEventListener("change", (event) => {
        if (event.target.matches("[data-elbysodic-gateway-curation-select]")) {
          updateGatewayCurationPositions(list);
          updateSpotlightComposer(list.closest("[data-elbysodic-spotlight-composer]"), true);
        }
      });

      list.addEventListener("dragstart", (event) => {
        const item = event.target.closest("[data-elbysodic-gateway-curation-item]");
        if (!item) {
          return;
        }
        item.setAttribute("aria-grabbed", "true");
        event.dataTransfer.effectAllowed = "move";
      });

      list.addEventListener("dragover", (event) => {
        const dragged = list.querySelector("[aria-grabbed='true']");
        if (!dragged) {
          return;
        }
        event.preventDefault();
        const target = gatewayCurationDropTarget(list, event.clientY);
        if (target) {
          list.insertBefore(dragged, target);
        } else {
          list.appendChild(dragged);
        }
        updateGatewayCurationPositions(list);
      });

      list.addEventListener("dragend", () => {
        const dragged = list.querySelector("[aria-grabbed='true']");
        if (dragged) {
          dragged.removeAttribute("aria-grabbed");
        }
        updateGatewayCurationPositions(list);
        updateSpotlightComposer(list.closest("[data-elbysodic-spotlight-composer]"), true);
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
    setupDiscoveryPreview(document);
    setupGatewayCuration(document);
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
