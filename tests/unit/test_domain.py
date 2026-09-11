from vgu_signal.domain import Source, SourceClass, TrustState, VerificationOutcome


def test_official_source_defaults_to_official_class() -> None:
    source = Source(id="x", name="VGU", url="https://vgu.ac.in/")
    assert source.source_class is SourceClass.OFFICIAL


def test_trust_states_include_required_paths() -> None:
    assert TrustState.VERIFIED.value == "VERIFIED"
    assert TrustState.CONFLICTING.value == "CONFLICTING"
    assert TrustState.UNVERIFIED.value == "UNVERIFIED"
    assert TrustState.SUPERSEDED.value == "SUPERSEDED"


def test_verification_outcomes_are_explicit() -> None:
    assert {item.value for item in VerificationOutcome} == {
        "VERIFIED",
        "CONFLICTING",
        "UNVERIFIED",
    }
