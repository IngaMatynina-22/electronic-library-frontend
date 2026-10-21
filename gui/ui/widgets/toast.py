from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class ToastHost(QWidget):
    """Simple stacked toast messages in the bottom-right of a parent."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 16, 16)
        self._layout.setSpacing(8)
        self._layout.addStretch(1)
        self.hide()

    def show_message(self, text: str, *, kind: str = "info", timeout_ms: int = 3500) -> None:
        toast = QFrame()
        toast.setObjectName("ContentSurface")
        row = QHBoxLayout(toast)
        row.setContentsMargins(12, 8, 12, 8)
        label = QLabel(text)
        label.setWordWrap(True)
        if kind == "error":
            label.setStyleSheet("color: #A63D3D; font-weight: 600;")
        elif kind == "success":
            label.setStyleSheet("color: #3D6B4F; font-weight: 600;")
        row.addWidget(label)
        self._layout.addWidget(toast)
        self.show()
        self.raise_()
        self._reposition()
        QTimer.singleShot(timeout_ms, lambda: self._remove(toast))

    def _remove(self, toast: QFrame) -> None:
        self._layout.removeWidget(toast)
        toast.deleteLater()
        if self._layout.count() <= 1:
            self.hide()

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        self.setFixedWidth(min(360, parent.width() - 32))
        self.adjustSize()
        self.move(parent.width() - self.width() - 8, parent.height() - self.height() - 28)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._reposition()
