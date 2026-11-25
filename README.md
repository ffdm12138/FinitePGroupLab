# FinitePGroupLab

**Finite p-group mathematics · Lean 4 / Mathlib · Auditable per-theorem formal releases**

An open-source release repository for independently checked mathematical results
arising from research on finite `p`-groups, including results connected to open
problems. The laboratory's runtime, experiments, private research state, and
unverified proof drafts live in a **different, non-public repository**.

**Release status:** The repository currently holds the verified publication
infrastructure only. **No theorem, proof, or open-problem solution is claimed by
this scaffold.** The published-result register is
[`releases/results.json`](releases/results.json) (`results: []`, `papers: []`).

## Organization / 目录结构（每个定理单开一个文件夹）

Every published theorem or lemma receives its **own dedicated folder** under
`problems/<Category>/<result-id>/` alongside a standalone Lean module under
`FinitePGroupLab/`:

| Scope | Result directory (one folder per theorem) | Standalone Lean source | Meaning |
| --- | --- | --- | --- |
| `P01` | [`problems/P01/`](problems/P01/README.md) | `FinitePGroupLab/Problems/P01/<Module>.lean` | Kourovka 21.114 / weakly ab-maximal groups |
| `P02` | [`problems/P02/`](problems/P02/README.md) | `FinitePGroupLab/Problems/P02/<Module>.lean` | Exact-order-`p` non-inner automorphisms |
| `P05` | [`problems/P05/`](problems/P05/README.md) | `FinitePGroupLab/Problems/P05/<Module>.lean` | Maximal conjugacy-class and kernel questions |
| `P07` | [`problems/P07/`](problems/P07/README.md) | `FinitePGroupLab/Problems/P07/<Module>.lean` | Related group and alternating-form investigations |
| `Pxx` | `problems/Pxx/<result-id>/` | `FinitePGroupLab/Problems/Pxx/<Module>.lean` | Any numbered open problem (`P00`–`P99`) |
| `Shared` | [`problems/Shared/`](problems/Shared/README.md) | `FinitePGroupLab/Shared/<Module>.lean` | Reusable structural lemmas shared across problems |
| `Thesis` | [`problems/Thesis/`](problems/Thesis/README.md) | `FinitePGroupLab/Thesis/<Module>.lean` | Verified theorems from the legacy thesis asset tree |

Inside each theorem folder `problems/<Category>/<result-id>/`:

```text
problems/<Category>/<result-id>/
  README.md         # exact statement S, domain assumptions, formal mapping
  proof.md          # complete human-readable mathematical proof
  metadata.json     # exact copy of the entry in releases/results.json
  HUMAN_REVIEW.md   # version-bound human sign-off (SHA256-locked)
  evidence/         # optional public-safe, redacted extracts (.md/.json/.txt)
```

For major breakthroughs or full-problem solutions (`FULL_PROBLEM`) that pass
all kernel, semantic, and Main acceptance gates, a curated paper package may
additionally live in `papers/<paper-id>/` (`README.md`, `metadata.json`,
`manuscript/`, `proof/`, `lean/PROOF_MAP.md`, `lean/PROOF_CHAIN.json`,
`review/HUMAN_REVIEW.md`, `reproduce/`), referencing its underlying released
theorems in `releases/results.json` without duplicating `.lean` source files.

Each public **result** must be a mathematically complete, precisely scoped
theorem or refutation, with a kernel-checked Lean proof (no `sorry`, `admit`,
`native_decide`, or unapproved axioms), a complete human-readable proof,
independently checked source-to-Lean semantics (`S ↔ L`), transitive parent
dependencies, source/build fingerprints, Main L4 acceptance, and **explicit
human sign-off for that exact frozen version before any GitHub push**. AI-agent
reviews alone do not count as human approval. A **local lemma** is never
presented as the **solution to the containing open problem**.

## Reproduce

The public project pins `leanprover/lean4:v4.34.0-rc1` with Mathlib revision
fixed in `lake-manifest.json`. After installing elan, Git, Python, and Lake:

```sh
lake exe cache get
python scripts/verify_lean_targets.py
python scripts/audit_release.py --all
python -m unittest discover -s scripts -p "test_*.py"
```

`verify_lean_targets.py` builds only the explicitly released Lean modules in
`releases/results.json` target-by-target (or verifies `FinitePGroupLab.lean`
when the manifest is empty), avoiding uncurated full-repository builds. Released
theorems must compile **in this standalone repository**, not merely in the
internal laboratory.

## Publication policy

Read [the publication checklist](docs/PUBLISHING.md),
[host migration notes](docs/MIGRATION.md), and
[the repository release gate](scripts/audit_release.py).
Before committing or pushing, verify `git status` and staged changes on the
`main` branch. Never push the private research repository or its historical Git
objects.

## 中文说明

本仓库为有限 `p` 群研究项目的**独立开源发布仓库**（私有研究主库位于另外的非公开仓库）：

- **每个定理单开一个文件夹**：公开发布的每条定理/引理独立存放在 `problems/<Category>/<result-id>/`（支持 `P00`–`P99`、`Shared`、`Thesis`），并配套唯一公开 Lean 真源 `FinitePGroupLab/.../*.lean` 与总清单 [`releases/results.json`](releases/results.json)。
- **重大突破论文包**：仅在完整问题或重大突破通过 L2 内核闭包、独立语义 L3、Main L4 及人类审签后，才可在 `papers/<paper-id>/` 组织论文与复现索引（不重复存放 `.lean` 副本）。
- **严格区分局部引理与公开问题全解**：原始私有库的 `.coord/`、SQLite、代理租约、未验证草稿、失败实验均**不会上传**。所有文本文件统一使用 **LF** 换行计算 SHA256 并在本仓库独立复现编译与人工签字后方可发布。

## License

The newly authored repository scaffold and original published code/docs are
made available under [MIT](LICENSE), unless a result explicitly documents
different applicable rights. Do not copy third-party PDFs, paper text, or
licensed files without checking their redistribution terms.
