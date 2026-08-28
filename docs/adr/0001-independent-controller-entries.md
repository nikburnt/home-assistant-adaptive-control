# Use one config entry and logical device per controller

Each Controller is represented by an independent Home Assistant config entry
and logical device, with an optional Area assignment used only for
organization. A singleton integration entry with controller subentries was
rejected because isolated lifecycle, reconfiguration, diagnostics, removal,
and migration are more important than a more compact integration card.
