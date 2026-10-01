from importlib.util import module_from_spec, spec_from_file_location
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "scripts" / "verification_assistant.py"
SPEC = spec_from_file_location("verification_assistant", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

Candidate = MODULE.Candidate
classify = MODULE.classify
score_submission = MODULE.score_submission


def candidate(statement: str, title: str = "Exam form deadline") -> Candidate:
    return Candidate(
        id="item-1",
        title=title,
        summary=statement,
        statement=statement,
        category="EXAM",
        source_url="https://vgu.ac.in/example",
        due_at="2026-10-15T00:00:00+00:00",
        starts_at=None,
        published_at="2026-10-01T00:00:00+00:00",
        claim_state="VERIFIED",
    )


def test_verification_match_scores_shared_content_and_date():
    score, reason = score_submission(
        "VGU exam form deadline 15/10/2026",
        candidate("VGU exam form submission deadline is 15/10/2026"),
    )
    assert score >= 0.35
    assert "matching date" in reason


def test_verification_does_not_treat_weak_overlap_as_confirmation():
    score, _ = score_submission("holiday notice", candidate("exam form deadline"))
    assert score < 0.35


def test_conflicting_matches_are_reviewable():
    item = candidate("exam form deadline")
    assert classify([(item, 0.7, "shared tokens")], {"item-1"}) == "CONFLICTING"


def test_no_match_is_unverified_not_false():
    assert classify([], set()) == "UNVERIFIED"
