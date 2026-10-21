"""Background task helpers using QThreadPool / QRunnable."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(object)
    progress = Signal(object)


class _Runnable(QRunnable):
    def __init__(self, fn: Callable, signals: WorkerSignals, args: tuple, kwargs: dict) -> None:
        super().__init__()
        self.fn = fn
        self.signals = signals
        self.args = args
        self.kwargs = kwargs
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(exc)


def run_in_thread(
    fn: Callable,
    *args: Any,
    on_finished: Callable | None = None,
    on_error: Callable | None = None,
    on_progress: Callable | None = None,
    **kwargs: Any,
) -> WorkerSignals:
    signals = WorkerSignals()
    if on_finished:
        signals.finished.connect(on_finished)
    if on_error:
        signals.error.connect(on_error)
    if on_progress:
        signals.progress.connect(on_progress)

    if kwargs.get("progress_callback") is True:
        kwargs["progress_callback"] = lambda *a, **k: signals.progress.emit(a[0] if a else k)

    runnable = _Runnable(fn, signals, args, kwargs)
    QThreadPool.globalInstance().start(runnable)
    return signals
