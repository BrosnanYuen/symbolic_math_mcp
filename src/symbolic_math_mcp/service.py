"""Core verification service used by the FastMCP tool."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Callable

from symbolic_math_verify import verify_yaml_file


Verifier = Callable[[str], str]


class SymbolicMathService:
    """Synchronously validate YAML files while enforcing queue and timeout limits."""

    def __init__(
        self,
        max_requests: int,
        total_timeout: float,
        verifier: Verifier = verify_yaml_file,
    ) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be greater than zero")
        if total_timeout <= 0:
            raise ValueError("total_timeout must be greater than zero")
        self._total_timeout = float(total_timeout)
        self._verifier = verifier
        self._slots = threading.Semaphore(max_requests)
        self._executor = ThreadPoolExecutor(max_workers=max_requests, thread_name_prefix="symbolic-math-verify")

    def shutdown(self) -> None:
        """Release executor resources."""
        self._executor.shutdown(wait=False, cancel_futures=True)

    def check_symbolic_math(self, filename: str) -> dict[str, str]:
        """Validate one YAML file and return the required synchronous response payload."""
        started = time.monotonic()
        normalized_name = str(filename)
        acquired = self._slots.acquire(timeout=self._total_timeout)
        if not acquired:
            return _timeout_response(normalized_name)
        try:
            path = Path(normalized_name)
            if path.suffix.lower() != ".yaml":
                return _file_not_found_response(normalized_name)
            if not path.exists() or not path.is_file():
                return _file_not_found_response(normalized_name)
            try:
                with path.open("r", encoding="utf-8"):
                    pass
            except FileNotFoundError:
                return _file_not_found_response(normalized_name)
            except OSError:
                return _file_read_error_response(normalized_name)

            remaining = self._total_timeout - (time.monotonic() - started)
            if remaining <= 0:
                return _timeout_response(normalized_name)

            future = self._executor.submit(self._verifier, normalized_name)
            try:
                result = future.result(timeout=remaining)
            except TimeoutError:
                future.cancel()
                return _timeout_response(normalized_name)
            except Exception:
                return _unknown_error_response(normalized_name)
            return _success_response(normalized_name, result)
        finally:
            self._slots.release()


def _success_response(filename: str, result: str) -> dict[str, str]:
    return {
        "status": "Tool call completed!",
        "filename": filename,
        "result": result,
    }


def _timeout_response(filename: str) -> dict[str, str]:
    return {
        "status": "Tool call has timed out!",
        "filename": filename,
        "result": "TIMEOUT ERROR!",
    }


def _file_not_found_response(filename: str) -> dict[str, str]:
    return {
        "status": "Tool call cannot find the file based on the filename!",
        "filename": filename,
        "result": "FILE NOT FOUND!",
    }


def _file_read_error_response(filename: str) -> dict[str, str]:
    return {
        "status": "Tool call cannot read the file!",
        "filename": filename,
        "result": "FILE CANNOT BE READ!",
    }


def _unknown_error_response(filename: str) -> dict[str, str]:
    return {
        "status": "Tool call has unknown error!",
        "filename": filename,
        "result": "UNKNOWN ERROR!",
    }
