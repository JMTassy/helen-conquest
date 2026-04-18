from __future__ import annotations
from typing import Callable, Any

WorkerFn = Callable[[dict[str, Any]], dict[str, Any]]

class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[str, WorkerFn] = {}

    def register(self, step_kind: str, fn: WorkerFn) -> None:
        self._workers[step_kind] = fn

    def get(self, step_kind: str) -> WorkerFn:
        if step_kind not in self._workers:
            raise KeyError(f"No worker registered for step_kind={step_kind}")
        return self._workers[step_kind]
