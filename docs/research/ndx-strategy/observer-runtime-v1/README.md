# Default-off observer image — isolated packaging verification

The active app Dockerfile omits docs/research assets and installs Python code into
site-packages. The existing research ROOT/SCHEMA constants assume a source tree;
an unmodified app image therefore cannot prove observer schema identity. This
separate image copies only dependency locks, source and the frozen research SQL,
and imports source through `/app/src`. No trading Dockerfile/configuration is
modified. Default command is the one-shot research CLI, still disabled unless
its explicit enable flag is true. No secrets/context/network/DB are supplied.

Before building, register the Dockerfile, complete copied source tree and locks
in a new build contract. Preserve resolved base-image build metadata, final image
ID and logs; tags are build inputs, never a claim of immutable runtime identity.
No project dependency pins change. Build only locally; do not push or deploy.

Run a uniquely named task-owned verification container with network=none,
read-only root, no capabilities, no-new-privileges, 256 MiB memory, 0.5 CPU,
64 PIDs, /tmp tmpfs and no secret/context mounts. Verify actual schema bytes/hash,
source ROOT, Python and SDK versions, then run the ordinary default command and
confirm `{status: disabled}` with exit zero. Neither check connects to a database,
requests gateway data, starts a worker or obtains credentials. Preserve stopped
containers and image identity, not an automatic activation or retry policy.

An immutable image ID is only a local intended release artifact. Named-target
transfer, secret/role provisioning, selected real universe/calendar/build/config
artifacts, broker state, storage reserve and current operational review remain
separate from these packaging checks. Do not invoke the default command of an
existing trading image as a packaging test; it starts `run_live`.
