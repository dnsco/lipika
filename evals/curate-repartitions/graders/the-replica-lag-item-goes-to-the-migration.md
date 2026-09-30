---
type: regex
target: trace
pattern: '(?i)replica(?:(?!\n).)*migrate-the-price-service-to-postgres'
---

The stale-prices thread's replica-lag item is sent to the migration thread, on the same line. It is
caused by the Postgres cutover, and the migration thread already tracks replica lag.
