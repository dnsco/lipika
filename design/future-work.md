---
type: reference
status: reference
tags: [vault, meta, design, future]
---

# Future work

Changes to the design that are ruled or still open, and not built. `vault-and-agent-ontology.md` describes
the system as it is; an entry here moves into it when the change ships, and leaves this file.

## Ruled, not built

_(nothing ruled and unbuilt)_

## Open questions

- **May a pickup write a dump?** A pickup confirms things nobody records until the next handoff, and a
  session that ends without one loses them. Appending to the orientation is ruled out — it is a view.
  The open shape is a pickup emitting a *record*. Against: it costs span, and read-only is that skill's
  strongest property. Dies when a pickup's findings are measurably lost, or read-only is judged worth it.
- **Does the routing note earn its place** beside the orientation, or does the index carry its one line?
- **What is the relevant fraction of a pickup** — of what it loads, how much bore on the work? It is the
  quantity this design claims to move, and it is unmeasured.
- **How stale is too stale?** Liveness and staleness use a 14-day window
  (`architecture-candidates --live-within-days`); it is a chosen parameter, not a measured one.
- **Does regenerating from the previous orientation plus new dumps lose items** that regenerating from
  all records would not? The loss is recoverable; its rate is unknown.
