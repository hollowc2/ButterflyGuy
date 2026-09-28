# Cohort automation

Keeps the open prospective execution-validation cohort filling itself.

- `butterfly-tunnel.service` — persistent SSH tunnel to the Helios TimescaleDB on
  `localhost:15432`, restarted automatically. The research code has no other route
  to the replay database.
- `butterfly-cohort-update.service` — runs `tools/cohort_daily_update.sh`, which
  appends completed sessions, verifies ledger integrity, then commits and pushes.
- `butterfly-cohort-update.timer` — weekdays at 18:30 PT (21:30 ET), after the close
  and after settlement data lands. `Persistent=true` catches missed runs after a
  reboot or suspend.

## Install

    install -Dm644 infra/systemd/butterfly-tunnel.service         ~/.config/systemd/user/butterfly-tunnel.service
    install -Dm644 infra/systemd/butterfly-cohort-update.service  ~/.config/systemd/user/butterfly-cohort-update.service
    install -Dm644 infra/systemd/butterfly-cohort-update.timer    ~/.config/systemd/user/butterfly-cohort-update.timer
    systemctl --user daemon-reload
    systemctl --user enable --now butterfly-tunnel.service butterfly-cohort-update.timer

Linger is already enabled for this user, so both survive logout.

## Check on it

    systemctl --user status butterfly-tunnel.service
    systemctl --user list-timers butterfly-cohort-update.timer
    tail -40 ~/.local/state/butterfly-cohort/update.log

## Known limitation: the SSH key

The ssh key is passphrase-protected and held by gpg-agent. The tunnel therefore needs
the key unlocked once per boot; until then the unit restarts in a loop and the update
skips. `git push` has the same dependency, so the script treats a failed push as a
warning and leaves the commit local rather than failing the run.

To remove this dependency entirely, use a dedicated passphrase-less key restricted to
the forward:

    ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_butterfly_tunnel -C butterfly-tunnel

then append its public key to `billy@helios:~/.ssh/authorized_keys` with a restriction:

    restrict,permitopen="127.0.0.1:5432" ssh-ed25519 AAAA... butterfly-tunnel

and add `-i ~/.ssh/id_butterfly_tunnel` to the tunnel unit's `ExecStart`. That key can
open only the database forward and run no commands.

## When the cohort closes

The cohort is frozen against source hashes. Any edit to the strategy, simulation
engine, or accounting modules makes `update` refuse to append, by design. Stop the
timer before starting strategy work:

    systemctl --user disable --now butterfly-cohort-update.timer
