# Observability

Every Controller and Signal Provider config entry exposes observability for its
own runtime without changing logging for other entries or integrations.

## Home Assistant entities

Each logical device includes:

- current-state entities for its effective profile, signal quality, override,
  safety, and other type-specific runtime state;
- a semantic event entity for meaningful decisions and transitions;
- a `Verbose Logging` configuration switch.

Controller entries also expose a restorable `Enabled` switch. It is off when a
controller is first installed, and disabling it preserves current actuator
state rather than issuing an implicit shutdown command.

`Verbose Logging` is off by default and its state is restored after a Home
Assistant restart. When it is on, detailed messages for only that Controller or
Signal Provider are promoted to the normal Home Assistant log. The switch does
not change the global logger level. Warnings and errors are always logged.

## Detailed logging

Verbose messages describe the decision path rather than dumping full Home
Assistant states. Depending on the entry type, they include:

- accepted input reports, aggregation results, and signal quality changes;
- profile candidates and the reason the effective profile was selected;
- profile requests, overrides, intervention policy, and safety arbitration;
- actuator commands, confirmations, retries, and rejected external changes;
- Signal Provider recomputation and publication decisions.

Credentials, tokens, and unbounded state attributes are never logged.

## Decision trace

Each entry also keeps a bounded in-memory decision trace for diagnostics. The
trace survives neither an integration reload nor a Home Assistant restart; it
exists to explain recent behavior without turning persistent logging on. A
semantic event may identify its related decision so an event can be correlated
with the trace and verbose log.
