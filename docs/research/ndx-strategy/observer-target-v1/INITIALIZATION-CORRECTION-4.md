# Initialized template extension — revision 4

Revision-3 compatibility run-06 proved final-server startup. Its 20 non-DB tests
passed, while 30 DB test fixtures errored because the fully initialized image
already installs TimescaleDB into template1. New databases inherit that extension.
The old fixture assumed it was absent, which held on the bootstrap-only server.
Preserve the run-06 test XML/logs and source copies.

Revision 4 uses `CREATE EXTENSION IF NOT EXISTS ... VERSION '2.25.2'` in the
isolated test fixture, followed by the existing exact server and extension version
assertions. A wrong installed version still fails. No production schema, privilege,
immutability, accounting assertion or resource limit is relaxed. The resource/
restore initializer already uses this exact identity-checking pattern.

Use `contract-v4.json` and `source-lock-v4.json`. Compatibility output is the new
`/tmp/ndx-timescale-observer-target/run-07`; resource/restore output remains the
unused `/tmp/ndx-target-resources-restore/run-02`. The programs and required
arguments otherwise match revision 3. Both run against final initialized servers,
with default container-only and private host-visible Unix sockets and TCP disabled.
