# Publish shared derived signals

Reusable or non-trivial derived observations are produced by independent
Signal Provider entries and exposed as ordinary Home Assistant entities.
Controllers may still bind directly to raw entities for simple cases, but they
never duplicate a shared calculation or call a provider directly; this keeps
dependencies explicit, makes history and diagnostics observable, and lets one
calculation be reused without coupling controller lifecycles.
