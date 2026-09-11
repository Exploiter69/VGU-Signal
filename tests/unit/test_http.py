from hashlib import sha256

from vgu_signal.acquisition.http import FetchError, FetchResult


def test_fetch_result_hash_is_sha256() -> None:
    result = FetchResult(
        url="https://vgu.ac.in/",
        status_code=200,
        content_type="text/html",
        body=b"hello",
        etag=None,
        last_modified=None,
    )
    assert result.raw_content_hash == sha256(b"hello").hexdigest()


def test_fetch_error_is_runtime_error() -> None:
    assert issubclass(FetchError, RuntimeError)
