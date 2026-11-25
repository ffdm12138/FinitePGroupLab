# Publication gate / 开源发布规范

## Two repositories, two different purposes

- **Private laboratory:** `C:\work\有限p群`. Preserves the direct mathematical
  asset tree (`FinitePGroups/*.lean` and co-located `*.proof.md`), `docs/registry/`,
  mutable `work/`, `.coord/` coordinator SQLite database, native build receipts,
  and source materials. It is **never** a GitHub release source.
- **Public Git repository:** `C:\work\有限p群\opensource\FinitePGroupLab`.
  This directory is its **own** Git root on branch `main`, with no inherited Git
  history or implicit synchronization with the laboratory. Its `origin` is
  `https://github.com/ffdm12138/FinitePGroupLab.git`; only curated,
  audit-passing materials belong here.

The internal repository ignores the entire `/opensource/` tree. Never push the
private repository or its Git history.

## Alignment with the Direct Math Asset Tree architecture

Under the laboratory's direct mathematical asset tree architecture (no legacy
`Research -> HAND -> PROMOTION -> IN_CORE` approval pipeline):

1. **Direct asset lineage:** Every candidate theorem originates from a stable
   `ASSET_ID` / `SOURCE_ID` node in `FinitePGroups/` (`*.lean` + adjacent
   `*.proof.md`), with explicit parent dependencies and real consumers.
2. **Source statement `S`:** Exact mathematical statement, quantifiers,
   domain assumptions, prime scope (including `p = 2` where applicable), and
   known primary-source provenance.
3. **Lean statement `L` and L2 kernel closure:** Full elaborated type and
   transitive dependency closure down to the pinned Mathlib revision and
   approved foundational Lean axioms (`propext`, `Classical.choice`,
   `Quot.sound`), with no `sorry`, `admit`, `sorryAx`, `native_decide`, or
   custom axioms. Must build **incrementally by target in this standalone
   public repository** (`scripts/verify_lean_targets.py`).
4. **Independent semantic review (L3):** A genuinely distinct reviewer audits
   `S ↔ L`, implicit binders/typeclasses, intermediate definitions, and domain
   fidelity. Disclose shared-host review honestly; never inflate AI checks into
   external mathematical endorsement.
5. **Main L4 acceptance:** Canonical same-version acceptance (`ASSET_ID`,
   source SHA256, dependency lock, axioms audit, real consumer). A task merely
   marked `DONE` is never sufficient.
6. **Human-readable exposition and formal link:** Complete mathematical proof
   in `proof.md` (and `papers/<paper-id>/`) following a two-stage readable
   structure: (a) open with a concise, high-signal **short proof / conceptual
   overview** explaining the global strategy and why it works; (b) immediately
   follow with the **full step-by-step mathematical proof** covering all
   lemmas, calculations, special cases, and literature comparisons. Avoid
   unexplained "notice that" / "obviously" / "suitably choose" jumps—explain
   *how* each key insight or construction was discovered (from examples,
   obstruction equations, failed attempts, or formalization feedback), never
   dumping raw Lean tactics. Any manuscript referencing the formalization must
   point explicitly to `https://github.com/ffdm12138/FinitePGroupLab`, the
   released `problems/<Category>/<result-id>/` folder, exact Lean constant FQN,
   and frozen `PROOF_CHAIN.json` / commit version (only after human approval and
   publication).
7. **Version-bound human sign-off before push:** A real human inspects the exact
   statement, readable proof, standalone Lean source, axioms, dependencies,
   scope, and license, then records identity, UTC time, and LF-byte SHA256
   digests in `HUMAN_REVIEW.md` and `releases/results.json`. AI agents may
   prepare packages and run hygiene gates, but never self-approve theorems or
   push unapproved mathematical results.

A result with `scope=LOCAL_LEMMA` must never claim the containing open problem
solved. `scope=FULL_PROBLEM` requires `original_domain_fully_covered=true`,
the full universal theorem over the original domain, closed L2/L3/L4 gates, and
primary-source novelty checking.

## Exact release folder contract

### 1. Per-theorem folder (every theorem gets its own folder)

Every released theorem or lemma has two matching entries registered in
`releases/results.json` (`"results"` array) and imported from `FinitePGroupLab.lean`:

```text
problems/<Category>/<stable-result-id>/
  README.md         exact theorem statement, assumptions, formal mapping
  proof.md          complete human-readable mathematical proof
  metadata.json     exact JSON object matching the manifest entry
  HUMAN_REVIEW.md   version-bound human sign-off for this frozen LF version
  evidence/         optional public-safe redacted extracts (.md/.json/.txt)

FinitePGroupLab/Problems/<Pxx>/<LeanModule>.lean   (for Category P00..P99)
FinitePGroupLab/Shared/<LeanModule>.lean           (for Category Shared)
FinitePGroupLab/Thesis/<LeanModule>.lean           (for Category Thesis)
```

Use `templates/RESULT_README.md`, `templates/RESULT_METADATA.example.json`,
and `templates/HUMAN_REVIEW_TEMPLATE.md` as templates only.

### 2. Breakthrough paper folder (optional, post-certification only)

Only after a major breakthrough or full open-problem certification (for P02,
same-version top-level `L2 + L3 + L4` across the entire original domain) may a
paper package be added under `papers/<paper-id>/` and registered under
`releases/results.json` (`"papers"` array):

```text
papers/<paper-id>/
  README.md
  metadata.json             exact JSON copy of manifest paper entry
  manuscript/               re-authored LaTeX/Markdown/BibTeX (.tex/.bib/.md/.cls/.sty)
  proof/                    complete human-readable mathematical proof (.md)
  lean/
    PROOF_MAP.md            human sections <-> exact Lean FQN mapping
    PROOF_CHAIN.json        pinned toolchain, modules, axioms, SHA256 closure
  review/HUMAN_REVIEW.md    version-bound human publication sign-off
  reproduce/README.md       targeted verification commands and build logs
```

Keep Lean source **single-sourced** in `FinitePGroupLab/{Problems,Shared,Thesis}/`:
`papers/<paper-id>/lean/` stores index/mapping files (`.md`/`.json`) only, never
duplicate `.lean` copies. Compiled PDFs, images, and LaTeX build artifacts are
forbidden from Git by `.gitignore` and `scripts/audit_release.py`.

## Line endings (LF) and SHA256 rule

All tracked text files use **LF** line endings per `.gitattributes`. On Windows,
always save files with LF before computing `source_sha256`,
`reviewed_source_sha256`, `reviewed_statement_sha256`, and
`review_record_sha256`. `scripts/audit_release.py --filesystem` rejects CRLF
bytes in LF-managed text files so working-tree digests always match Git index
(`--staged`) and Linux CI (`--all`).

## Setup, verification, and publication

```powershell
cd "C:\work\有限p群\opensource\FinitePGroupLab"
git status --short
python scripts/audit_release.py --filesystem
python scripts/audit_release.py --staged
python -m unittest discover -s scripts -p "test_*.py"
python scripts/verify_lean_targets.py --dry-run
git remote -v   # must point ONLY to https://github.com/ffdm12138/FinitePGroupLab.git
```

When committing on `main` (set your Git identity first):

```powershell
git config --local user.name "YOUR_GITHUB_NAME"
git config --local user.email "YOUR_GITHUB_NOREPLY_EMAIL"
git add README.md LICENSE .gitignore .gitattributes
git add lean-toolchain lakefile.toml lake-manifest.json FinitePGroupLab.lean
git add .github .githooks scripts docs templates releases problems
python scripts/audit_release.py --staged
python -m unittest discover -s scripts -p "test_*.py"
git diff --cached --stat
git commit -m "Initialize FinitePGroupLab public release framework"
git push -u origin main
```

- **Scaffold vs theorem commits:** Pushing the empty-manifest infrastructure
  scaffold (`results: []`, `papers: []`) publishes the repository layout,
  gates, and documentation only; it makes zero mathematical claims.
- **Theorem & paper releases:** Each actual theorem folder or paper package
  requires its own completed L2/L3/L4 gates, standalone targeted Lean build,
  fresh `HUMAN_REVIEW.md` sign-off, clean `audit_release.py`, and explicit human
  push decision. Never copy from the private lab via `robocopy /MIR`,
  `git subtree`, `git push --mirror`, or `git push --force`.
- **Target-only Lean verification:** Both local reproduction and GitHub Actions
  run `scripts/verify_lean_targets.py` to build explicitly released Lean targets
  incrementally (no uncurated umbrella/full-lab Lake builds).

## Hardening and limits

- Git ignore rules do not erase files already committed in Git history; keep
  private files out of every commit.
- `scripts/audit_release.py` is an allowlist, LF, manifest, and heuristic secret
  gate; always inspect `git diff --cached` and enable GitHub secret scanning /
  push protection.
- CI verifies Lean compilation in the standalone public repo; it does **not**
  verify mathematical semantics (`S ↔ L`), priority, or human consent.
