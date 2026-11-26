from src.retry import RetryPolicy, with_retries

def test_with_retries_eventually_succeeds():
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("transient")
        return "ok"

    wrapped = with_retries(fn, RetryPolicy(max_retries=4, base_seconds=0.0, max_seconds=0.0))
    assert wrapped() == "ok"
    assert calls["n"] == 3

def test_with_retries_raises_after_max():
    calls = {"n": 0}
    def fn():
        calls["n"] += 1
        raise TimeoutError("transient")

    wrapped = with_retries(fn, RetryPolicy(max_retries=2, base_seconds=0.0, max_seconds=0.0))
    try:
        wrapped()
        assert False, "Expected TimeoutError"
    except TimeoutError:
        assert calls["n"] == 2
