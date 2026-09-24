# Bengal handbook scaffold

The handbook's canonical content stays in `docs/product/`,
`docs/architecture/`, and `docs/operations/`. `scripts/bengal_docs.py` stages
only those reader-facing sections for Bengal, so `docs/AGENTS.md` remains a
contributor instruction file rather than published handbook content.

The adapter also contains two bounded Bengal 0.5.1 compatibility measures:

- its CLI build path currently hard-codes a `content/` directory after loading
  the configured `docs/` content directory;
- its default theme emits RSS and root Markdown references that an undated docs
  site does not generate.

The static empty RSS channel and root Markdown copy keep `bengal audit` strict.
Remove these measures once the pinned Bengal release produces the same clean
artifact without them.

Search uses Bengal's generated `index.json` at runtime. The optional Python
Lunr prebuild is disabled because Bengal 0.5.1 cannot prebuild this handbook's
index; the default theme documents and supports the runtime fallback.

Python autodoc is intentionally not enabled: Elbysodic does not currently
declare a stable public Python API, so publishing implementation modules would
create a contract the package is not promising.

The CI lane uploads `public/` as a review artifact. Public hosting remains a
separate, approval-gated deployment decision.
