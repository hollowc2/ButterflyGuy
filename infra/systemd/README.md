# Cohort automation

Keeps the SPX v2 prospective execution-validation cohort filling itself. Use these
units from the dedicated v2 checkout; the v1 automation is retired.

- `butterfly-tunnel.service` — persistent SSH tunnel to the Helios TimescaleDB on
  `localhost:15432`, restarted automatically. The research code has no other route
  to the replay database.
- `butterfly-cohort-v2-update.service` — runs `tools/cohort_daily_update.sh`, which
  appends completed sessions, verifies ledger integrity, then commits and pushes.
  It runs from `/mnt/Repos/Trading/Butterflyguy/.worktrees/spx-prospective-v2` on
  branch `cohort/spx-prospective-v2-2026-10-02`, with the registration frozen at
  `8b276f1`. Ledger commits go to that branch, never to `main`, so research work on
  `main` cannot make the frozen sources drift. Merge the branch into `main` when you
  want the ledger there.
  The copy on `main` is a reporting snapshot. Its frozen-source check can report
  drift as `main` changes; verify and append from the dedicated cohort worktree.
  Keep the cohort branch and worktree until the study closes.
- `butterfly-cohort-v2-update.timer` — weekdays at 18:30 PT (21:30 ET), after the close
  and after settlement data lands. `Persistent=true` catches missed runs after a
  reboot or suspend.

## Install

    install -Dm644 infra/systemd/butterfly-tunnel.service         ~/.config/systemd/user/butterfly-tunnel.service
    install -Dm644 infra/systemd/butterfly-cohort-v2-update.service  ~/.config/systemd/user/butterfly-cohort-v2-update.service
    install -Dm644 infra/systemd/butterfly-cohort-v2-update.timer    ~/.config/systemd/user/butterfly-cohort-v2-update.timer
    systemctl --user daemon-reload
    systemctl --user enable --now butterfly-tunnel.service butterfly-cohort-v2-update.timer

Linger is already enabled for this user, so both survive logout.

## Check on it

    systemctl --user status butterfly-tunnel.service
    systemctl --user list-timers butterfly-cohort-v2-update.timer
    tail -40 ~/.local/state/butterfly-cohort-v2/update.log

## Retired v1

The installed `butterfly-cohort-update.service` and `.timer` definitions were
removed and both names masked on October 1, 2026. They are inactive and cannot be
started or enabled while masked. Their old definitions remain in Git history.
The v1 branch, checkout at `/mnt/Repos/Trading/Butterflyguy-cohort`, manifest,
ledgers and update log are retained solely as the closed study's audit record.
Do not reinstall or unmask the retired v1 automation.

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

    systemctl --user disable --now butterfly-cohort-v2-update.timer
