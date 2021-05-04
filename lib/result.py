from typing import Literal, Optional


class Result:
    raw_result: bytes
    error: Optional[str] = None

    def __init__(self, raw_result: bytes, raw_error: bytes) -> None:
        self.raw_result = raw_result
        err = raw_error.decode('utf-8')
        if err:
            self.error = err

    @property
    def result(self) -> str:
        return self.raw_result.decode('utf-8')

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def state(self) -> Literal['success', 'error']:
        if self.success:
            return 'success'
        return 'error'
