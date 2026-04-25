# Changelog Fragments

Add one fragment per user-visible change:

```text
changelog.d/+short-description.added.md
changelog.d/+short-description.changed.md
changelog.d/+short-description.deprecated.md
changelog.d/+short-description.removed.md
changelog.d/+short-description.fixed.md
changelog.d/+short-description.security.md
```

Fragment text should be a complete sentence without a leading dash. Compile the
final changelog with `make changelog`, or preview it with `make changelog-draft`.
