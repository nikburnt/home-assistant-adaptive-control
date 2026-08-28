# Persist intent and recompute after restart

Controllers persist active profile requests, overrides, safety-cycle timing,
the last effective profile, and transition-action execution markers across a
Home Assistant restart. On setup they discard expired intent, read current
inputs and actuators, apply their type-specific startup policy, and compute a
new effective profile; persisted automatic output is never treated as the
source of truth, and transition actions are not replayed solely because the
integration restarted.
