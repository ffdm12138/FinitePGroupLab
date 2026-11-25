# <Precise mathematical title>

**Category:** `P0X` / `Shared` / `Thesis`
**Release ID:** `<stable-result-id>`
**Private Asset ID / Source ID:** `<ASSET_ID>` / `<SOURCE_ID>`
**Scope:** `LOCAL_LEMMA` or `FULL_PROBLEM`
**Status:** `RELEASED_VERIFIED` (only after independent verification)

## Exact statement

Write the complete mathematical assertion, all implicit assumptions,
all quantifiers and the exact statement of any counterexample.

## Short proof overview & detailed human-readable proof

Start [`proof.md`](proof.md) with a concise **short proof / conceptual
overview** that highlights the global strategy, then immediately follow with
the **full step-by-step proof** with no hidden steps. Avoid unexplained
"notice that" / "obviously" phrases—explicitly explain *how* each key
construction or observation was found, and distinguish new ideas from prior
results and heuristic insight.

## Formal mapping

- Public repository pointer: `https://github.com/ffdm12138/FinitePGroupLab` (`problems/<Category>/<stable-result-id>/`)

- Public Lean source: `FinitePGroupLab/Problems/P0X/<Result>.lean` (or `Shared/` / `Thesis/`)
- Exact full Lean constant: `FinitePGroupLab.Problems.P0X.<name>`
- Pinned toolchain / Mathlib revision: `leanprover/lean4:v4.34.0-rc1` / `de5ce8a9...`
- Actual elaborated type / binder comparison:
- Direct released parent results and transitive kernel dependencies:
- Recursive axioms (`#print axioms`) and allowed kernel dependencies:
- Standalone targeted Lake check (`verify_lean_targets.py`) and receipt:
- Same-source-version independent semantic review (`S ↔ L`):
- Main acceptance identity and version:
- Human reviewer and exact frozen LF-version approval: `HUMAN_REVIEW.md`
- Distinguish a local lemma from a global open-problem solution.

## Limitations, provenance, and references

List what remains unproved, applicable domain restrictions, references,
source licenses, and how the result differs from published work.
Never include private worker data or unpublished personal information.
