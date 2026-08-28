# Snapshot illuminance when occupancy starts

Presence Lighting selects its occupied daytime profile from the illuminance
observed when occupancy starts and retains that profile until vacancy or a
night-state transition. Continuous lux-based switching was rejected because
the controller's own light output can raise the sensor reading and create an
on/off feedback loop. Input quality continues to update while occupied, but
ordinary lux changes do not replace the retained profile.
