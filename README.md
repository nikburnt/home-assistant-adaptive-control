# Adaptive Control

Adaptive Control is a Home Assistant custom integration for independent,
typed Controllers and reusable Signal Providers. It is intended for adaptive
behavior whose decisions need explicit inputs, actuator ownership, observable
state, and diagnostics beyond a collection of unrelated automations.

## Current status

The repository currently contains the shared runtime and observability
foundation:

- typed Controller and Signal Provider entry kinds;
- one bounded in-memory decision trace per config entry;
- credentials-free config-entry diagnostics;
- a restorable per-entry **Verbose logging** configuration switch;
- HACS, Hassfest, Ruff, and Home Assistant test configuration.

No Controller Types are exposed through the Home Assistant UI yet. The first
configuration flow will ship with the first concrete Controller Type so every
created entry has valid input roles, policy, and owned actuators.

## Model

Each Controller is an independent Home Assistant config entry and logical
device. A Controller consumes explicitly bound Signals and owns the Actuators
it commands. Signal Providers are separate entries that publish reusable
derived Signals without commanding Actuators.

The accepted language and relationships are defined in [CONTEXT.md](CONTEXT.md).
Architecture decisions live under [docs/adr](docs/adr), and the common logging
and diagnostics contract is described in
[docs/observability.md](docs/observability.md).

## Installation

This initial foundation is not yet intended for installation on a production
Home Assistant instance. HACS metadata is present so validation and release
packaging remain part of development from the beginning.

## Development

The current test baseline is Home Assistant 2026.8.1 on Python 3.14.

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m pytest -q
ruff check custom_components tests
ruff format --check custom_components tests
```

## License

[MIT](LICENSE)
