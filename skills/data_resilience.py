import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_operation(op_name: str, fn: Callable[[], T], attempts: int = 3, delay_s: float = 0.4) -> T:
    """
    Shared resilience helper for upstream data providers.
    Applies bounded retries with linear backoff and raises a typed RuntimeError.
    """
    last_err = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:
            last_err = exc
            if i < attempts - 1:
                time.sleep(delay_s * (i + 1))
    raise RuntimeError(f"{op_name} failed after {attempts} attempts: {last_err}") from last_err

