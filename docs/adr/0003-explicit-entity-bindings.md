# Require explicit entity bindings

Areas filter and rank configuration suggestions, but every input and actuator
binding is explicitly confirmed and stored. Controllers never adopt newly
discovered area entities automatically; this trades one-time setup convenience
for predictable ownership and prevents physical fallback sources, diagnostics,
or newly added devices from silently changing controller behavior.
