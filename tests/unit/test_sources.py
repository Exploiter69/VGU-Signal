from vgu_signal.sources.registry import SOURCES, get_source


def test_phase1_registry_contains_high_value_official_sources() -> None:
    assert {
        "vgu-resources",
        "vgu-examination-rules",
        "vgu-public-notice",
        "vgu-fees",
        "vgu-events",
    } <= set(SOURCES)
    assert all(source.enabled for source in SOURCES.values())
    assert all(source.source_class.value == "OFFICIAL" for source in SOURCES.values())


def test_registry_lookup_is_strict() -> None:
    assert str(get_source("vgu-fees").url) == "https://vgu.ac.in/admission/fee-structure"
    try:
        get_source("missing")
    except KeyError as exc:
        assert str(exc) == "'unknown source: missing'"
    else:
        raise AssertionError("missing source must fail closed")
