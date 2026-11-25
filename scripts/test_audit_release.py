"""Regression tests for the independent public-release allowlist and target runner."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit_release import (
    LEAN_UNTRUSTED,
    SECRET_PATTERNS,
    check_manifest,
    valid_path,
)
from verify_lean_targets import lean_module_name, planned_commands


def make_released_item(
    rid: str = "tested-local-lemma",
    problem: str = "P01",
    lean_file: str = "FinitePGroupLab/Problems/P01/Example.lean",
    lean_constant: str = "FinitePGroupLab.Problems.P01.example",
    source: bytes = b"namespace FinitePGroupLab.Problems.P01\n theorem example : True := trivial\nend FinitePGroupLab.Problems.P01\n",
    review_text: bytes = b"# Human review\nReviewer: actual-human-for-fixture\nApproved scope: toy local statement\n",
) -> tuple[dict, dict[str, bytes]]:
    item = {
        "id": rid,
        "problem": problem,
        "scope": "LOCAL_LEMMA",
        "status": "RELEASED_VERIFIED",
        "title": "A toy local statement for the manifest test",
        "statement": "True",
        "lean_file": lean_file,
        "lean_constant": lean_constant,
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "build_receipt": "STANDALONE_B2_ID",
        "axioms_review": "RECURSIVE_AXIOMS_REVIEW_ID",
        "semantic_review": "INDEPENDENT_SEMANTIC_REVIEW_ID",
        "main_acceptance": "FORMAL_MAIN_ACCEPTANCE_ID",
        "human_review": {
            "decision": "APPROVED_FOR_PUBLIC_RELEASE",
            "reviewer": "Actual human (synthetic test fixture)",
            "reviewed_at_utc": "2026-11-13T00:00:00Z",
            "review_scope": "Toy statement/source/proof/public rights",
            "reviewed_source_sha256": hashlib.sha256(source).hexdigest(),
            "reviewed_statement_sha256": hashlib.sha256(b"True").hexdigest(),
            "review_record_sha256": hashlib.sha256(review_text).hexdigest(),
        },
        "literature_status": "CHECKED_WITH_PRIMARY_SOURCES",
        "original_domain_fully_covered": False,
    }
    mod = lean_file.removesuffix(".lean").replace("/", ".")
    docbase = f"problems/{problem}/{rid}/"
    files = {
        "FinitePGroupLab.lean": f"import {mod}\n".encode("ascii"),
        lean_file: source,
        "releases/results.json": json.dumps({
            "schema": "FinitePGroupLabReleaseIndexV1", "results": [item], "papers": [],
        }).encode(),
        docbase + "README.md": b"statement",
        docbase + "proof.md": b"proof",
        docbase + "HUMAN_REVIEW.md": review_text,
        docbase + "metadata.json": json.dumps(item).encode(),
    }
    return item, files


class PublicReleaseGateTests(unittest.TestCase):
    def test_only_exact_public_proof_paths(self):
        self.assertTrue(valid_path("FinitePGroupLab/Problems/P02/VerifiedLemma.lean"))
        self.assertTrue(valid_path("FinitePGroupLab/Shared/CommonLemma.lean"))
        self.assertTrue(valid_path("FinitePGroupLab/Thesis/ChapterOneLemma.lean"))
        self.assertTrue(valid_path("problems/P02/verified-lemma/metadata.json"))
        self.assertTrue(valid_path("problems/Shared/common-lemma/HUMAN_REVIEW.md"))
        self.assertTrue(valid_path("problems/Thesis/chapter-one-lemma/evidence/axioms.txt"))
        self.assertTrue(valid_path("papers/p02-full-solution/manuscript/main.tex"))
        self.assertTrue(valid_path("papers/p02-full-solution/lean/PROOF_MAP.md"))
        self.assertTrue(valid_path("papers/p02-full-solution/lean/PROOF_CHAIN.json"))
        self.assertTrue(valid_path("papers/p02-full-solution/review/HUMAN_REVIEW.md"))
        for name in (
            "work/session/FRONTIER-R6/private.json",
            ".coord/state.sqlite",
            "archive/notes.md",
            "problems/P02/unpaid/PRIVATE_CLAIM.txt",
            "docs/../private.txt",
            "FinitePGroupLab/Problems/P02/source.pdf",
            "problems/P02/secret-token/.env",
            "papers/p02-full-solution/manuscript/main.pdf",
            "papers/p02-full-solution/lean/DuplicateCopy.lean",
            "papers/p02-full-solution/drafts/notes.md",
        ):
            self.assertFalse(valid_path(name), name)

    def test_lean_untrusted_terms(self):
        self.assertIsNotNone(LEAN_UNTRUSTED.search("theorem a : True := by\n  sorry\n"))
        self.assertIsNotNone(LEAN_UNTRUSTED.search("axiom oracle : False\n"))

    def test_token_like_text_is_rejected(self):
        fake_example = b"gh" + b"p_" + b"x" * 26
        self.assertTrue(any(p.search(fake_example) for p in SECRET_PATTERNS))

    @staticmethod
    def empty_index():
        return {"releases/results.json": json.dumps({
            "schema": "FinitePGroupLabReleaseIndexV1", "results": [], "papers": [],
        }).encode(), "FinitePGroupLab.lean": b"import Mathlib\n"}

    def test_empty_public_release_is_truthful(self):
        errors = []
        check_manifest(self.empty_index(), errors)
        self.assertEqual(errors, [])

    def test_unlisted_lean_and_result_folder_are_blocked(self):
        files = self.empty_index()
        files["FinitePGroupLab/Problems/P02/DRAFT.lean"] = b"theorem t : True := trivial\n"
        files["problems/P02/unlisted-theorem/README.md"] = b"draft\n"
        errors = []
        check_manifest(files, errors)
        self.assertTrue(any("lacks released metadata" in e for e in errors))
        self.assertTrue(any("Result directory lacks released metadata" in e for e in errors))

    def test_full_problem_requires_full_domain(self):
        files = self.empty_index()
        item = {
            "id": "proof-example",
            "problem": "P02",
            "scope": "FULL_PROBLEM",
            "status": "RELEASED_VERIFIED",
            "title": "Example title",
            "statement": "Example statement",
            "lean_file": "FinitePGroupLab/Problems/P02/Example.lean",
            "lean_constant": "FinitePGroupLab.Problems.P02.example",
            "source_sha256": "0" * 64,
            "build_receipt": "build1",
            "axioms_review": "axioms1",
            "semantic_review": "review1",
            "main_acceptance": "main1",
            "literature_status": "CHECKED_WITH_PRIMARY_SOURCES",
            "original_domain_fully_covered": False,
        }
        files["releases/results.json"] = json.dumps({
            "schema": "FinitePGroupLabReleaseIndexV1", "results": [item],
        }).encode()
        errors = []
        check_manifest(files, errors)
        self.assertTrue(any("unsupported full-problem claim" in e for e in errors))

    def test_complete_local_metadata_and_shared_scope_consistent(self):
        _, files = make_released_item()
        errors = []
        check_manifest(files, errors)
        self.assertEqual(errors, [])

        _, shared_files = make_released_item(
            rid="shared-helper",
            problem="Shared",
            lean_file="FinitePGroupLab/Shared/Helper.lean",
            lean_constant="FinitePGroupLab.Shared.helper",
        )
        errors = []
        check_manifest(shared_files, errors)
        self.assertEqual(errors, [])

        # Even a previously valid release is refused if the human approval
        # record is missing or silently changed after approval.
        review_path = "problems/P01/tested-local-lemma/HUMAN_REVIEW.md"
        files.pop(review_path)
        errors = []
        check_manifest(files, errors)
        self.assertTrue(any("human review record missing" in e for e in errors))
        files[review_path] = b"modified after human approval"
        errors = []
        check_manifest(files, errors)
        self.assertTrue(any("human review record hash mismatch" in e for e in errors))

    def test_paper_package_requires_released_results_and_human_review(self):
        item, files = make_released_item(rid="p02-main-theorem", problem="P02",
                                         lean_file="FinitePGroupLab/Problems/P02/MainTheorem.lean",
                                         lean_constant="FinitePGroupLab.Problems.P02.main")
        chain = b'{"root": "FinitePGroupLab.Problems.P02.main"}\n'
        paper_review = b"# Paper review\nDecision: APPROVED_FOR_PUBLIC_RELEASE\n"
        paper = {
            "id": "p02-breakthrough-paper",
            "problem": "P02",
            "status": "RELEASED_VERIFIED",
            "title": "Exact-order-p non-inner automorphisms",
            "statement": "Full P02 statement",
            "result_ids": ["p02-main-theorem"],
            "proof_chain_sha256": hashlib.sha256(chain).hexdigest(),
            "main_acceptance": "MAIN_L4_ID",
            "literature_status": "CHECKED_WITH_PRIMARY_SOURCES",
            "human_review": {
                "decision": "APPROVED_FOR_PUBLIC_RELEASE",
                "reviewer": "Actual human (synthetic test fixture)",
                "reviewed_at_utc": "2026-11-25T00:00:00Z",
                "review_scope": "Manuscript, human proof, proof chain, rights",
                "reviewed_proof_chain_sha256": hashlib.sha256(chain).hexdigest(),
                "reviewed_statement_sha256": hashlib.sha256(b"Full P02 statement").hexdigest(),
                "review_record_sha256": hashlib.sha256(paper_review).hexdigest(),
            },
        }
        files["releases/results.json"] = json.dumps({
            "schema": "FinitePGroupLabReleaseIndexV1", "results": [item], "papers": [paper],
        }).encode()
        files.update({
            "papers/p02-breakthrough-paper/README.md": b"# Paper\n",
            "papers/p02-breakthrough-paper/metadata.json": json.dumps(paper).encode(),
            "papers/p02-breakthrough-paper/manuscript/main.tex": b"\\documentclass{article}\n",
            "papers/p02-breakthrough-paper/proof/human-readable-proof.md": b"# Proof\n",
            "papers/p02-breakthrough-paper/lean/PROOF_MAP.md": b"# Map\n",
            "papers/p02-breakthrough-paper/lean/PROOF_CHAIN.json": chain,
            "papers/p02-breakthrough-paper/review/HUMAN_REVIEW.md": paper_review,
            "papers/p02-breakthrough-paper/reproduce/README.md": b"# Reproduce\n",
        })
        errors = []
        check_manifest(files, errors)
        self.assertEqual(errors, [])

        # Unlisted paper directory must fail closed.
        files["papers/unapproved-draft/README.md"] = b"draft\n"
        errors = []
        check_manifest(files, errors)
        self.assertTrue(any("Paper directory lacks released metadata" in e for e in errors))

    def test_target_only_lean_commands(self):
        self.assertEqual(lean_module_name("FinitePGroupLab/Problems/P02/Foo.lean"),
                         "FinitePGroupLab.Problems.P02.Foo")
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "results.json"
            manifest.write_text('{"schema":"FinitePGroupLabReleaseIndexV1","results":[],"papers":[]}',
                                encoding="utf-8")
            self.assertEqual(
                planned_commands(manifest),
                [["lake", "env", "lean", "FinitePGroupLab.lean"]],
            )
            manifest.write_text(json.dumps({
                "schema": "FinitePGroupLabReleaseIndexV1",
                "results": [
                    {"lean_file": "FinitePGroupLab/Shared/A.lean"},
                    {"lean_file": "FinitePGroupLab/Problems/P02/B.lean"},
                ],
            }), encoding="utf-8")
            self.assertEqual(
                planned_commands(manifest, lake_cmd="/elan/lake"),
                [
                    ["/elan/lake", "build", "FinitePGroupLab.Shared.A"],
                    ["/elan/lake", "build", "FinitePGroupLab.Problems.P02.B"],
                    ["/elan/lake", "env", "lean", "FinitePGroupLab.lean"],
                ],
            )


if __name__ == "__main__":
    unittest.main()
