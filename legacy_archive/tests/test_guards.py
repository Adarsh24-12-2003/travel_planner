from src.guards import safe_call, GuardError
from pydantic import BaseModel

class M(BaseModel):
    x: int

def test_safe_call_validates_output():
    out = safe_call("t", lambda: {"x": 1}, expect_model=M)
    assert isinstance(out, M)
    assert out.x == 1

def test_safe_call_wraps_exception():
    try:
        safe_call("boom", lambda: 1/0)
        assert False, "Expected GuardError"
    except GuardError as e:
        assert "boom" in str(e)
