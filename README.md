# Adaptive Control

Adaptive Control is a Home Assistant custom integration for independent,
typed Controllers and reusable Signal Providers. It is intended for adaptive
behavior whose decisions need explicit inputs, actuator ownership, observable
state, and diagnostics beyond a collection of unrelated automations.

## Current status

The repository contains the shared runtime and the first Controller Type,
**Presence Lighting**:

- typed Controller and Signal Provider entry kinds;
- one bounded in-memory decision trace per config entry;
- credentials-free config-entry diagnostics;
- restorable per-entry **Enabled** and **Verbose logging** switches;
- effective-profile and input-quality sensors;
- a semantic decision event;
- UI setup and reconfiguration for explicit entity bindings;
- HACS, Hassfest, Ruff, and Home Assistant test configuration.

Presence Lighting uses occupancy, an explicit night-state entity, and an
illuminance snapshot taken when occupancy starts. The night state can be
`sun.sun` or a reusable on/off context such as an `input_boolean`, binary
sensor, or schedule. It owns one stateful main-light actuator and activates
profile transition scenes once per real profile change.

| Effective profile | Main light | Transition scene |
| --- | --- | --- |
| `vacant` | Off | Vacant scene |
| `occupied_bright` | Off | Occupied scene |
| `occupied_dark` | On | Occupied scene |
| `occupied_night` | Off | Night occupied scene |

The controller starts disabled on first installation. Missing occupancy,
night state, or required daytime illuminance produces `input_unavailable` and
preserves current outputs instead of guessing. A valid vacancy remains safe to
process without the other signals.

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

Add this repository to HACS as a custom integration repository, install
**Adaptive Control**, and restart Home Assistant. Add the integration and bind:

- one occupancy binary sensor;
- one illuminance sensor;
- `sun.sun` or an on/off helper as the night-state signal;
- one main `light` or `switch` actuator;
- occupied, night-occupied, and vacant scenes;
- an optional Home Assistant Area and the low-light threshold.

Review the created logical device, then turn on **Enabled**. The controller does
not issue actuator or scene commands before that switch is enabled.

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
