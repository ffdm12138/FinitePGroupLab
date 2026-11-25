#!/usr/bin/env python3
"""Fail-closed release-contents audit for the independent public repository.

This is a hygiene gate, not a replacement for Lean, mathematical review,
GitHub secret scanning, or a human reading the entire staged diff.

Modes:
  --filesystem  inspect the current public directory (before first git add)
  --staged      inspect the *whole Git index*, not the mutable worktree
  --all         inspect the *whole Git index* (CI and pre-push)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024

ROOT_FILES = {
    ".gitignore", ".gitattributes", "LICENSE", "README.md",
    "lakefile.toml", "lake-manifest.json", "lean-toolchain",
    "FinitePGroupLab.lean",
}
FORBIDDEN_SEGMENTS = {
    ".git", ".lake", ".coord", "work", "research", "article",
    "archive", "audit", "human_check", "scratch", "tmp",
    "output", "drafts", "staging", "__pycache__",
    ".venv", "private", "secrets", "credentials",
}
FORBIDDEN_SUFFIXES = {
    ".sqlite", ".db", ".wal", ".shm", ".zip", ".7z", ".rar",
    ".pem", ".p12", ".pfx", ".key", ".exe", ".dll", ".olean",
    ".ilean", ".pdf", ".png", ".jpg", ".jpeg", ".gif",
    ".aux", ".log", ".out", ".toc", ".gz", ".fls", ".fdb_latexmk",
}
LF_MANAGED_SUFFIXES = {
    ".md", ".py", ".lean", ".toml", ".json", ".yml", ".yaml",
    ".sh", ".tex", ".bib", ".cls", ".sty",
}
LF_MANAGED_PATHS = {
    ".gitignore", ".gitattributes", ".githooks/pre-commit", ".githooks/pre-push",
}
FORBIDDEN_NAME_PARTS = (
    "worker_private", "private_claim", "lease_token", "password",
    "credential", "secret_token", "access_token", "id_rsa",
    "id_ed25519", "worker_lease", "state.sqlite",
)
# Literal strings here deliberately avoid containing sample working credentials.
SECRET_PATTERNS = [
    re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"sk-[A-Za-z0-9_-]{25,}"),
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(rb"https?://[A-Za-z0-9_.%+-]+:[^/\s@]+@"),
    re.compile(rb"(?i)(?:api[_-]?key|client[_-]?secret|auth[_-]?token)\s*[:=]\s*['\x22][^'\x22\s]{12,}"),
]
LEAN_UNTRUSTED = re.compile(r"\b(sorry|admit|sorryAx|native_decide)\b|^\s*axiom\b", re.MULTILINE)
CATEGORY_RE = re.compile(r"(?:P[0-9]{2}|Shared|Thesis)\Z")
PROBLEM_NUM_RE = re.compile(r"P[0-9]{2}\Z")
RESULT_ID = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
LEAN_STEM_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")


def expected_lean_prefix(category: str) -> str:
    """Return the canonical Lean directory prefix for a problem/category."""
    if PROBLEM_NUM_RE.fullmatch(category):
        return f"FinitePGroupLab/Problems/{category}/"
    return f"FinitePGroupLab/{category}/"


def is_public_lean_source(path: str) -> bool:
    p = PurePosixPath(path)
    parts = p.parts
    if p.suffix != ".lean" or not LEAN_STEM_RE.fullmatch(p.stem):
        return False
    if len(parts) == 4 and parts[0] == "FinitePGroupLab" and parts[1] == "Problems" and PROBLEM_NUM_RE.fullmatch(parts[2]):
        return True
    if len(parts) == 3 and parts[0] == "FinitePGroupLab" and parts[1] in {"Shared", "Thesis"}:
        return True
    return False


def valid_paper_path(parts: tuple[str, ...], suffix: str, name: str) -> bool:
    if len(parts) < 3 or parts[0] != "papers" or not RESULT_ID.fullmatch(parts[1]):
        return False
    if len(parts) == 3:
        return name in {"README.md", "metadata.json"}
    section = parts[2]
    if section == "manuscript":
        return suffix in {".tex", ".bib", ".md", ".cls", ".sty"}
    if section == "proof":
        return suffix == ".md"
    if section == "lean":
        # Papers index PROOF_MAP.md / PROOF_CHAIN.json only; never duplicate .lean sources.
        return suffix in {".md", ".json"}
    if section == "review":
        return suffix in {".md", ".json"}
    if section == "reproduce":
        return suffix in {".md", ".json", ".txt", ".py", ".sh"}
    return False


def valid_path(path: str) -> bool:
    p = PurePosixPath(path)
    parts = p.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        return False
    if p.is_absolute() or "\\" in path:
        return False
    lower = [part.lower() for part in parts]
    if any(x in FORBIDDEN_SEGMENTS for x in lower):
        return False
    if any(word in p.name.lower() for word in FORBIDDEN_NAME_PARTS):
        return False
    if p.suffix.lower() in FORBIDDEN_SUFFIXES:
        return False

    if path in ROOT_FILES:
        return True
    if path in {".githooks/pre-commit", ".githooks/pre-push"}:
        return True
    if path == ".github/workflows/ci.yml":
        return True
    if path == "releases/results.json":
        return True
    if len(parts) == 2 and parts[0] == "scripts" and p.suffix == ".py":
        return True
    if len(parts) == 2 and parts[0] == "docs" and p.suffix == ".md":
        return True
    if len(parts) == 2 and parts[0] == "templates" and p.suffix in {".md", ".json"}:
        return True
    if len(parts) >= 3 and parts[0] == "problems" and CATEGORY_RE.fullmatch(parts[1]):
        if len(parts) == 3 and p.name == "README.md":
            return True
        if len(parts) == 4 and RESULT_ID.fullmatch(parts[2]) and p.name in {
            "README.md", "proof.md", "metadata.json", "HUMAN_REVIEW.md",
        }:
            return True
        if (len(parts) == 5 and RESULT_ID.fullmatch(parts[2]) and
                parts[3] == "evidence" and p.suffix in {".md", ".json", ".txt"}):
            return True
    if parts[0] == "papers":
        return valid_paper_path(parts, p.suffix, p.name)
    if is_public_lean_source(path):
        return True
    return False


def git_output(*args: str) -> bytes:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError("Git index is unavailable; run --filesystem first")
    return proc.stdout


def list_index() -> dict[str, bytes]:
    files = [x.decode("utf-8") for x in git_output("ls-files", "--cached", "-z").split(b"\0") if x]
    return {path: git_output("show", ":" + path) for path in files}


def list_filesystem() -> dict[str, bytes]:
    out = {}
    for f in ROOT.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(ROOT)
        if any(part in {".git", ".lake", "__pycache__"} for part in rel.parts):
            continue
        out[rel.as_posix()] = f.read_bytes()
    return out


def check_human_review(
    review: object,
    human_md_path: str,
    files: dict[str, bytes],
    *,
    artifact_review_key: str,
    artifact_sha: object,
    statement: object,
    label: str,
    errors: list[str],
) -> None:
    """Validate version-bound HUMAN_REVIEW metadata and record SHA256."""
    if not isinstance(review, dict):
        errors.append(f"{label}: human review missing")
        return
    if review.get("decision") != "APPROVED_FOR_PUBLIC_RELEASE":
        errors.append(f"{label}: human approval not granted")
    for key in ("reviewer", "reviewed_at_utc", "review_scope"):
        if not isinstance(review.get(key), str) or not review[key].strip():
            errors.append(f"{label}: human review {key} missing")
    if review.get(artifact_review_key) != artifact_sha:
        errors.append(f"{label}: human review {artifact_review_key} mismatch")
    if statement is not None:
        if not isinstance(statement, str) or review.get("reviewed_statement_sha256") != hashlib.sha256(
            statement.encode("utf-8")
        ).hexdigest():
            errors.append(f"{label}: human review statement version mismatch")
    human_bytes = files.get(human_md_path)
    if human_bytes is None:
        errors.append(f"{label}: human review record missing")
    elif review.get("review_record_sha256") != hashlib.sha256(human_bytes).hexdigest():
        errors.append(f"{label}: human review record hash mismatch")


def check_optional_provenance(item: dict[str, object], label: str, errors: list[str]) -> None:
    """Type-check optional Direct Math Asset Tree fields when present."""
    for str_field in ("asset_id", "source_id", "lean_toolchain", "mathlib_rev", "paper_id"):
        val = item.get(str_field)
        if val is not None and (not isinstance(val, str) or not val.strip()):
            errors.append(f"{label}: invalid {str_field}")
    axioms = item.get("approved_axioms")
    if axioms is not None and (
        not isinstance(axioms, list) or not all(isinstance(x, str) and x.strip() for x in axioms)
    ):
        errors.append(f"{label}: invalid approved_axioms")
    parents = item.get("parent_results")
    if parents is not None and (
        not isinstance(parents, list) or not all(isinstance(x, str) and x.strip() for x in parents)
    ):
        errors.append(f"{label}: invalid parent_results")


def check_papers_manifest(
    papers: object,
    released_result_ids: set[str],
    files: dict[str, bytes],
    errors: list[str],
) -> None:
    if papers is None:
        papers = []
    if not isinstance(papers, list):
        errors.append("Manifest papers must be a list")
        return

    seen_paper_ids: set[str] = set()
    for i, paper in enumerate(papers):
        if not isinstance(paper, dict):
            errors.append(f"Paper #{i}: not an object")
            continue
        pid, problem = paper.get("id"), paper.get("problem")
        if not isinstance(pid, str) or not RESULT_ID.fullmatch(pid):
            errors.append(f"Paper #{i}: bad ID")
            continue
        if not isinstance(problem, str) or not CATEGORY_RE.fullmatch(problem):
            errors.append(f"Paper {pid}: bad problem ID")
            continue
        if pid in seen_paper_ids:
            errors.append(f"Repeated paper ID: {pid}")
        seen_paper_ids.add(pid)
        if paper.get("status") != "RELEASED_VERIFIED":
            errors.append(f"Paper {pid}: not formally released")
        if paper.get("literature_status") != "CHECKED_WITH_PRIMARY_SOURCES":
            errors.append(f"Paper {pid}: missing literature check")
        result_ids = paper.get("result_ids")
        if not isinstance(result_ids, list) or not result_ids or not all(
            isinstance(x, str) and x in released_result_ids for x in result_ids
        ):
            errors.append(f"Paper {pid}: result_ids must reference released manifest results")
        for field in ("title", "statement", "proof_chain_sha256", "main_acceptance"):
            if not isinstance(paper.get(field), str) or not paper[field].strip():
                errors.append(f"Paper {pid}: missing {field}")

        base = f"papers/{pid}/"
        for req in (
            "README.md", "metadata.json", "lean/PROOF_MAP.md",
            "lean/PROOF_CHAIN.json", "review/HUMAN_REVIEW.md", "reproduce/README.md",
        ):
            if base + req not in files:
                errors.append(f"Paper {pid}: missing {base + req}")
        if not any(p.startswith(base + "manuscript/") for p in files):
            errors.append(f"Paper {pid}: missing manuscript files")
        if not any(p.startswith(base + "proof/") for p in files):
            errors.append(f"Paper {pid}: missing proof files")

        chain_bytes = files.get(base + "lean/PROOF_CHAIN.json")
        if chain_bytes is not None and hashlib.sha256(chain_bytes).hexdigest() != paper.get("proof_chain_sha256"):
            errors.append(f"Paper {pid}: PROOF_CHAIN.json SHA256 mismatch")

        if base + "metadata.json" in files:
            try:
                if json.loads(files[base + "metadata.json"].decode("utf-8")) != paper:
                    errors.append(f"Paper {pid}: metadata != release manifest entry")
            except (UnicodeError, json.JSONDecodeError):
                errors.append(f"Paper {pid}: invalid metadata JSON")

        check_human_review(
            paper.get("human_review"),
            base + "review/HUMAN_REVIEW.md",
            files,
            artifact_review_key="reviewed_proof_chain_sha256",
            artifact_sha=paper.get("proof_chain_sha256"),
            statement=paper.get("statement"),
            label=f"Paper {pid}",
            errors=errors,
        )

    actual_paper_ids = {
        PurePosixPath(p).parts[1]
        for p in files
        if p.startswith("papers/") and len(PurePosixPath(p).parts) >= 2
    }
    for unlisted in sorted(actual_paper_ids - seen_paper_ids):
        errors.append(f"Paper directory lacks released metadata: papers/{unlisted}/")


def check_manifest(files: dict[str, bytes], errors: list[str]) -> None:
    try:
        manifest = json.loads(files["releases/results.json"].decode("utf-8"))
    except (KeyError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"Invalid public release manifest: {exc}")
        return
    if manifest.get("schema") != "FinitePGroupLabReleaseIndexV1":
        errors.append("Unexpected public release manifest schema")
        return
    results = manifest.get("results")
    if not isinstance(results, list):
        errors.append("Manifest results must be a list")
        return
    seen_ids: set[str] = set()
    declared_folders: set[tuple[str, str]] = set()
    declared_sources: set[str] = set()
    for i, result in enumerate(results):
        if not isinstance(result, dict):
            errors.append(f"Result #{i}: not an object")
            continue
        rid, problem = result.get("id"), result.get("problem")
        if not isinstance(rid, str) or not RESULT_ID.fullmatch(rid):
            errors.append(f"Result #{i}: bad ID")
            continue
        if not isinstance(problem, str) or not CATEGORY_RE.fullmatch(problem):
            errors.append(f"Result {rid}: bad problem ID")
            continue
        if rid in seen_ids:
            errors.append(f"Repeated release ID: {rid}")
        seen_ids.add(rid)
        declared_folders.add((problem, rid))
        if result.get("status") != "RELEASED_VERIFIED":
            errors.append(f"Result {rid}: not formally released")
        if result.get("scope") not in {"LOCAL_LEMMA", "FULL_PROBLEM"}:
            errors.append(f"Result {rid}: invalid scope")
        if result.get("scope") == "FULL_PROBLEM" and result.get("original_domain_fully_covered") is not True:
            errors.append(f"Result {rid}: unsupported full-problem claim")
        if result.get("literature_status") != "CHECKED_WITH_PRIMARY_SOURCES":
            errors.append(f"Result {rid}: missing literature check")

        required = ("title", "statement", "lean_file", "lean_constant",
                    "build_receipt", "axioms_review", "semantic_review",
                    "main_acceptance")
        for field in required:
            if not isinstance(result.get(field), str) or not result[field].strip():
                errors.append(f"Result {rid}: missing {field}")
        check_optional_provenance(result, f"Result {rid}", errors)

        lean_path = result.get("lean_file")
        if not isinstance(lean_path, str):
            continue
        if not lean_path.startswith(expected_lean_prefix(problem)) or not lean_path.endswith(".lean"):
            errors.append(f"Result {rid}: inconsistent Lean module path")
        declared_sources.add(lean_path)
        src = files.get(lean_path)
        if src is None:
            errors.append(f"Result {rid}: Lean file absent from public Git index")
        elif hashlib.sha256(src).hexdigest() != result.get("source_sha256"):
            errors.append(f"Result {rid}: public Lean source SHA256 mismatch")

        docbase = f"problems/{problem}/{rid}/"
        for path in [docbase + "README.md", docbase + "proof.md",
                     docbase + "metadata.json", docbase + "HUMAN_REVIEW.md"]:
            if path not in files:
                errors.append(f"Result {rid}: missing {path}")
        check_human_review(
            result.get("human_review"),
            docbase + "HUMAN_REVIEW.md",
            files,
            artifact_review_key="reviewed_source_sha256",
            artifact_sha=result.get("source_sha256"),
            statement=result.get("statement"),
            label=f"Result {rid}",
            errors=errors,
        )

        if docbase + "metadata.json" in files:
            try:
                metadata = json.loads(files[docbase + "metadata.json"].decode("utf-8"))
                if metadata != result:
                    errors.append(f"Result {rid}: metadata != release manifest entry")
            except (UnicodeError, json.JSONDecodeError):
                errors.append(f"Result {rid}: invalid metadata JSON")

        module_name = lean_path.removesuffix(".lean").replace("/", ".")
        if (b"import " + module_name.encode("ascii")) not in files.get("FinitePGroupLab.lean", b""):
            errors.append(f"Result {rid}: not imported from public root file")

    actual_sources = {p for p in files if is_public_lean_source(p)}
    for unlisted in sorted(actual_sources - declared_sources):
        errors.append(f"Lean proof file lacks released metadata: {unlisted}")

    actual_folders = {
        (PurePosixPath(p).parts[1], PurePosixPath(p).parts[2])
        for p in files
        if p.startswith("problems/") and len(PurePosixPath(p).parts) >= 4
    }
    for cat, rid in sorted(actual_folders - declared_folders):
        errors.append(f"Result directory lacks released metadata: problems/{cat}/{rid}/")

    check_papers_manifest(manifest.get("papers"), seen_ids, files, errors)


def run(mode: str) -> int:
    try:
        files = list_filesystem() if mode == "filesystem" else list_index()
    except (RuntimeError, OSError, UnicodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    errors: list[str] = []
    size_sum = 0
    for path, content in files.items():
        if not valid_path(path):
            errors.append(f"Forbidden public path: {path}")
            continue
        if len(content) > MAX_FILE_BYTES:
            errors.append(f"File exceeds 5 MiB: {path}")
        size_sum += len(content)
        if b"\0" in content:
            errors.append(f"Non-text/binary file: {path}")
        if (path in LF_MANAGED_PATHS or PurePosixPath(path).suffix in LF_MANAGED_SUFFIXES) and b"\r\n" in content:
            errors.append(f"CRLF line ending in LF-enforced file (convert to LF before computing SHA256): {path}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                errors.append(f"Potential credential in: {path} (details withheld)")
                break
        if path == "FinitePGroupLab.lean" or is_public_lean_source(path):
            if LEAN_UNTRUSTED.search(content.decode("utf-8", errors="replace")):
                errors.append(f"Untrusted Lean proof construct: {path}")
    if size_sum > MAX_TOTAL_BYTES:
        errors.append("Total published content exceeds 32 MiB")
    for mandatory in ROOT_FILES | {"releases/results.json"}:
        if mandatory not in files:
            errors.append(f"Required public file missing: {mandatory}")
    check_manifest(files, errors)
    if errors:
        print("PUBLIC_RELEASE_GATE_FAIL")
        for e in errors:
            print(" - " + e)
        return 1
    print(f"PUBLIC_RELEASE_GATE_PASS mode={mode} files={len(files)} bytes={size_sum}")
    print("NOTE: human review, mathematical semantic verification, and clean Lean CI remain mandatory.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--filesystem", action="store_true")
    group.add_argument("--staged", action="store_true")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    sys.exit(run("filesystem" if args.filesystem else ("staged" if args.staged else "all")))
