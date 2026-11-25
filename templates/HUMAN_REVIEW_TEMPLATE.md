# Human publication review — template only

> **STOP: This template is not an approval.** An AI agent may prepare a
> review package but must never fill out a human approval as if a person
> had actually inspected and agreed to publish. A real reviewer must make
> the decision, then update this file or provide the actual signed record.

- Result or Paper ID (`<stable-result-id>` / `<paper-id>`):
- Private Asset ID / Source ID (`ASSET_ID` / `SOURCE_ID`):
- Exact original mathematical statement S:
- Exact Lean theorem L (fully elaborated binders):
- Frozen public Lean source SHA256 (LF bytes) or `PROOF_CHAIN.json` SHA256:
- Frozen mathematical statement SHA256 (UTF-8):
- Locked Lean / Mathlib version (`lean-toolchain` / `lake-manifest.json`):
- Independent S↔L semantic review report:
- Targeted Kernel/Lake build and allowed recursive axioms evidence:
- Complete human-readable proof (`proof.md` or `papers/<id>/proof/`) and all major branches reviewed:
- Previous literature, priority wording, sources and copyright reviewed:
- No private data or credentials and no unfinished proof leaked:
- Scope: `LOCAL_LEMMA` or `FULL_PROBLEM` (do not confuse them):
- Actual reviewing human's name or accountable reviewer identifier:
- Review date and time (UTC):
- Decision: `APPROVED_FOR_PUBLIC_RELEASE` or `REJECTED`
- Exactly which frozen source + statement versions were examined:
- Corrections or limitations:

Only after a genuine human decision and version-bound review should a
publication maintainer transfer the real approval fields to
`metadata.json` and the matching entry in `releases/results.json`.
Ensure this file is saved with **LF** line endings before computing
`review_record_sha256`. The release checker compares SHA256 values and file
existence but **cannot authenticate that an AI did not fabricate human
consent**. Final commit review and push must therefore be initiated or
explicitly authorized by the human owner.
