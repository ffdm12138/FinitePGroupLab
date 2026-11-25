# 24/7 workstation migration / 全天候科研主机迁移

**Two separate transports:**
the complete **private** runtime moves by an authenticated offline/secure
backup, whereas GitHub holds **only** the curated public `FinitePGroupLab`
code and documents. Never use GitHub as a private SQLite/checkpoint backup.

## Safe migration order

1. On the old host, identify the sole running Main, its child worker leases,
   coordinator Build Broker and active single-Lake work. Obtain an authorized,
   durable checkpoint. Avoid killing active jobs or changing lease/SQLite
   tables manually; stop dispatch via the project's approved control plane.
2. Verify the latest task/lease/fence IDs, sidecars, committed proof source
   fingerprints, Build receipts and WAL state. Do not copy an inconsistent
   live SQLite file; use the supported SQLite online backup API or take a
   quiescent copy with its required WAL sidecars.
3. Back up the **entire** internal repository with private records and working
   history, including otherwise ignored `work/`, `.coord/` and runtime
   manifests. Preserve file hashes and protect transport/storage encryption.
   Exclude only rebuildable large `.lake/` after verifying its contents are
   regenerable. Keep an untouched old-host rollback copy.
4. Install Git, Python, elan, Lean and the correct Mathlib version on the new
   host; keep `lean-toolchain` and `lake-manifest.json` identical. Restore
   the appropriate registered Serena/Tunnel configuration and remote project
   path. The **same database must have exactly one active Main writer**.
5. Before starting new research, run the documented read-only coordinator
   status/doctor checks; compare task/lease/build counts and current proof
   SHA, test small locked-version Lean modules through the authorized single
   Broker, and repair stale leases by the Main's sanctioned API only.
6. Restore continuous operation with approved service/task scheduling,
   power recovery, no sleep, logging, monitoring and explicit model budget
   controls. A powered-on machine or Serena watchdog cannot revive a
   terminated cloud AI session; true 24/7 agent execution requires a
   separately configured durable agent scheduler with authorization.
7. Preserve the private `master` branch and frozen evidence. Do not blindly
   merge two divergent live database copies or run two Lake builders against
   the same production state.
8. Copy the independent `opensource/FinitePGroupLab` directory along with
   the lab, or clone **its public GitHub repository** into that path after
   authentication. GitHub is not the source of internal research state.

## Independent public repository on the new host

If copying the public directory, `.git/` stays with it and retains only its
own **fresh** commits. Run:

```powershell
cd "C:\work\有限p群\opensource\FinitePGroupLab"
git rev-parse --show-toplevel
git remote -v
gh auth status
python scripts/audit_release.py --all
python -m unittest discover -s scripts -p "test_*.py"
lake exe cache get
python scripts/verify_lean_targets.py
```

Use the `main` branch for public changes. Set `git config --local user.name`
and `user.email` for the public repo, without writing credentials to source.
If the new host's private repo has an `origin`, do not push it.

**Do not perform this migration while the current Main is actively executing.**
This is a handoff runbook, not evidence that migration has occurred.
