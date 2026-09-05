const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const composerSource = fs.readFileSync(
  "src/elbysodic/web/static/elbysodic-composer.js",
  "utf8",
);

function createStorage() {
  const values = new Map();
  return {
    values,
    get length() {
      return values.size;
    },
    getItem(key) {
      return values.has(key) ? values.get(key) : null;
    },
    key(index) {
      return Array.from(values.keys())[index] || null;
    },
    removeItem(key) {
      values.delete(key);
    },
    setItem(key, value) {
      values.set(key, String(value));
    },
  };
}

function loadComposer({ config, storage = createStorage(), href, fields = {} }) {
  const factories = {};
  const replacedUrls = [];
  const window = {
    _chirpAlpineData(name, factory) {
      factories[name] = factory;
    },
    history: {
      state: null,
      replaceState(_state, _title, url) {
        replacedUrls.push(url);
      },
    },
    localStorage: storage,
  };
  if (href) {
    window.location = { href, origin: new URL(href).origin };
  }
  const context = {
    URL,
    URLSearchParams,
    console,
    document: {
      addEventListener() {},
      getElementById(id) {
        if (id === "config") {
          return { textContent: JSON.stringify(config) };
        }
        return fields[id] || null;
      },
    },
    window,
  };
  vm.runInNewContext(composerSource, context);
  return { context, factories, replacedUrls, storage };
}

function makeComposer(loaded, token = "") {
  const composer = loaded.factories.elbysodicComposer("config");
  const watchers = {};
  composer.$nextTick = (callback) => callback();
  composer.$root = {
    querySelector() {
      return token ? { value: token } : null;
    },
  };
  composer.$watch = (name, callback) => {
    watchers[name] = callback;
  };
  return { composer, watchers };
}

const baseConfig = {
  characters: [{ id: 1 }, { id: 2 }],
  draftKey: "reply:7:11",
  mentionEndpoint: "/mentionables/search",
  selectedCharacterId: 1,
};

test("face switches save outgoing empty and nonempty drafts and initialize a missing face", () => {
  const loaded = loadComposer({ config: baseConfig });
  const { composer, watchers } = makeComposer(loaded);
  composer.init();

  composer.body = "Rogue's private reply";
  watchers.body();
  composer.selectedCharacterId = "2";
  watchers.selectedCharacterId("2", "1");

  assert.equal(composer.body, "");
  assert.equal(composer.title, "");
  assert.deepEqual(JSON.parse(loaded.storage.values.get("elbysodic:draft:reply:7:11:1")), {
    version: 2,
    body: "Rogue's private reply",
    title: "",
  });
  assert.deepEqual(JSON.parse(loaded.storage.values.get("elbysodic:draft:reply:7:11:2")), {
    version: 2,
    body: "",
    title: "",
  });

  composer.body = "Logan's private reply";
  watchers.body();
  composer.body = "";
  watchers.body();
  composer.selectedCharacterId = "1";
  watchers.selectedCharacterId("1", "2");

  assert.equal(composer.body, "Rogue's private reply");
  assert.deepEqual(JSON.parse(loaded.storage.values.get("elbysodic:draft:reply:7:11:2")), {
    version: 2,
    body: "",
    title: "",
  });

  composer.selectedCharacterId = "2";
  watchers.selectedCharacterId("2", "1");
  assert.equal(composer.body, "");
  assert.equal(composer.draftState, "restored");
});

test("a matching redirect receipt removes the exact submitted draft across destinations", () => {
  const storage = createStorage();
  const origin = loadComposer({ config: baseConfig, storage });
  const { composer } = makeComposer(origin, "token-123");
  composer.body = "Posted exactly once";
  composer.submitDraft();

  assert.equal(storage.values.size, 1);
  loadComposer({
    config: { ...baseConfig, draftKey: "reply:7:created-thread" },
    storage,
    href: "https://realm.test/boards/danger-room/threads/new-thread?view=latest&draft_ack=token-123#post-1",
  });

  assert.equal(storage.values.size, 0);
});

test("a corrupt null record cannot block receipt cleanup for a later valid record", () => {
  const storage = createStorage();
  storage.setItem("elbysodic:draft:reply:7:corrupt:1", "null");
  const origin = loadComposer({ config: baseConfig, storage });
  const { composer } = makeComposer(origin, "token-after-corrupt");
  composer.body = "Valid submitted draft";
  composer.submitDraft();

  const destination = loadComposer({
    config: baseConfig,
    storage,
    href: "https://realm.test/boards/danger-room/threads/scene?draft_ack=token-after-corrupt#post-8",
  });

  assert.equal(storage.values.get("elbysodic:draft:reply:7:corrupt:1"), "null");
  assert.equal(storage.values.has("elbysodic:draft:reply:7:11:1"), false);
  assert.deepEqual(destination.replacedUrls, ["/boards/danger-room/threads/scene#post-8"]);
});

test("a redirect receipt preserves edits made after the submitted snapshot and strips itself", () => {
  const storage = createStorage();
  const origin = loadComposer({ config: baseConfig, storage });
  const { composer } = makeComposer(origin, "token-newer");
  composer.body = "Submitted snapshot";
  composer.submitDraft();
  composer.body = "Submitted snapshot plus a newer paragraph";
  composer.saveDraft();

  const destination = loadComposer({
    config: baseConfig,
    storage,
    href: "https://realm.test/boards/danger-room/threads/scene?draft_ack=token-newer&view=latest#post-8",
  });

  const retained = JSON.parse(storage.values.get("elbysodic:draft:reply:7:11:1"));
  assert.equal(retained.body, "Submitted snapshot plus a newer paragraph");
  assert.equal(retained.submitted, undefined);
  assert.deepEqual(destination.replacedUrls, [
    "/boards/danger-room/threads/scene?view=latest#post-8",
  ]);
});

test("storage failures leave the composer usable and report that autosave is unavailable", () => {
  const storage = {
    getItem() {
      throw new Error("SecurityError");
    },
    removeItem() {
      throw new Error("SecurityError");
    },
    setItem() {
      throw new Error("SecurityError");
    },
  };
  const loaded = loadComposer({ config: baseConfig, storage });
  const { composer, watchers } = makeComposer(loaded);

  assert.doesNotThrow(() => composer.init());
  assert.deepEqual(Object.keys(watchers).sort(), ["body", "selectedCharacterId", "title"]);
  composer.body = "Rogue remains private in memory";
  watchers.body();
  composer.selectedCharacterId = "2";
  watchers.selectedCharacterId("2", "1");
  assert.equal(composer.body, "");
  composer.body = "Logan remains private in memory";
  watchers.body();
  composer.selectedCharacterId = "1";
  watchers.selectedCharacterId("1", "2");
  assert.equal(composer.body, "Rogue remains private in memory");
  assert.equal(composer.draftStatusText(), "Draft autosave unavailable.");
});

test("body mentions apply only the latest request generation", async () => {
  const bodyField = { selectionStart: 3 };
  const loaded = loadComposer({ config: baseConfig, fields: { body: bodyField } });
  const { composer } = makeComposer(loaded);
  const requests = [];
  loaded.context.fetch = () => new Promise((resolve) => requests.push(resolve));

  composer.body = "@al";
  const older = composer.searchBodyMention("body");
  composer.body = "@bo";
  const newer = composer.searchBodyMention("body");
  requests[1]({
    json: async () => ({ items: [{ handle: "bob", id: 2, kind: "character" }] }),
    ok: true,
  });
  await newer;
  requests[0]({
    json: async () => ({ items: [{ handle: "alice", id: 1, kind: "character" }] }),
    ok: true,
  });
  await older;

  assert.equal(composer.bodyMentionResults.length, 1);
  assert.equal(composer.bodyMentionResults[0].handle, "bob");
});

test("closing body mentions invalidates a pending response", async () => {
  const bodyField = { selectionStart: 3 };
  const loaded = loadComposer({ config: baseConfig, fields: { body: bodyField } });
  const { composer } = makeComposer(loaded);
  const requests = [];
  loaded.context.fetch = () => new Promise((resolve) => requests.push(resolve));

  composer.body = "@al";
  composer.bodyMentionOpen = true;
  const pending = composer.searchBodyMention("body");
  composer.closeBodyMention();
  requests[0]({
    json: async () => ({ items: [{ handle: "alice", id: 1, kind: "character" }] }),
    ok: true,
  });
  await pending;

  assert.equal(composer.bodyMentionOpen, false);
  assert.equal(composer.bodyMentionResults.length, 0);
});

test("standalone mention picker applies only the latest request generation", async () => {
  const loaded = loadComposer({
    config: { endpoint: "/mentionables/search", scope: "all", selected: [] },
  });
  const picker = loaded.factories.elbysodicMentionPicker("config");
  const requests = [];
  loaded.context.fetch = () => new Promise((resolve) => requests.push(resolve));

  picker.query = "al";
  const older = picker.search();
  picker.query = "bo";
  const newer = picker.search();
  requests[1]({
    json: async () => ({ items: [{ handle: "bob", id: 2, kind: "character" }] }),
    ok: true,
  });
  await newer;
  requests[0]({
    json: async () => ({ items: [{ handle: "alice", id: 1, kind: "character" }] }),
    ok: true,
  });
  await older;

  assert.equal(picker.results.length, 1);
  assert.equal(picker.results[0].handle, "bob");
});

test("closing the standalone picker invalidates a pending response", async () => {
  const loaded = loadComposer({
    config: { endpoint: "/mentionables/search", scope: "all", selected: [] },
  });
  const picker = loaded.factories.elbysodicMentionPicker("config");
  const requests = [];
  loaded.context.fetch = () => new Promise((resolve) => requests.push(resolve));

  picker.query = "al";
  picker.open = true;
  const pending = picker.search();
  picker.close();
  requests[0]({
    json: async () => ({ items: [{ handle: "alice", id: 1, kind: "character" }] }),
    ok: true,
  });
  await pending;

  assert.equal(picker.open, false);
  assert.equal(picker.results.length, 0);
  assert.equal(picker.loading, false);
});
